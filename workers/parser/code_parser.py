"""
코드 파싱 코드

9/15
합의: ast 또는 정규식으로 함수/클래스/주석 단위 분할.
연동: preprocess.py → nodes.py

ast로 최상위 함수/클래스를 줄 번호가 붙은 Chunk로 만드는 코드입니다
ast.parse 가 실패하는 파일은 고정 줄 수 슬라이딩 윈도우로 폴백합니다.
Graph Node(`parse_files_node`)는 아직 이 함수만 호출하면 됩니다!

ast란? 파이썬 표준 라이브러리 제공되는 모듈

소스 코드의 구조를 트리(나무) 형태로 표현한 것입니다.
컴파일러나 인터프리터가 코드를 실행하기 전에,
텍스트로 된 코드를 분석하기 쉬운 자료구조로 바꾼 결과물이라고 보면 된다.
"""

from __future__ import annotations

import ast
from pathlib import Path

from schemas.files import Chunk, FileInfo

"""
함수 하나가 청크 경계에서 두 동강 나버리면
나중에 이 청크를 검색하거나 RAG(검색 증강 생성)에 
사용할 때 문맥이 끊겨서 의미를 파악하기 어려워진다.

겹치는 구간(10줄)을 두면 경계에 걸린 코드 블록이 최소 한쪽 청크에는 
완전한 형태로 포함될 가능성이 높아지기 때문에 문맥 손실을 줄이기 위한 안전장치임
"""

# 파싱 실패 , 즉 ast.parse 실패 시 폴백 창 크기와 이동 폭 설정 , 창이 겹치는 만큼 경계에 걸린 코드가 살아남
FALLBACK_WINDOW_LINES = 60
FALLBACK_STRIDE_LINES = 50


"""
이건 타입 별칭(Type Alias) 을 만드는 문법 "Destination이라는 이름은 ast.FunctionDef 
또는 ast.AsyncFunctionDef 또는 ast.ClassDef 중 하나를 의미한다"
파이썬 3.10부터 지원하는 Union 타입 문법입니다 

ast 모듈에서 코드를 파싱하면, 함수/클래스 정의는 각각 다른 노드 타입으로 표현됩니다
즉, "코드를 어떤 단위로 자를지"의 기준을 한 곳에 모아둔 것입니다.
"""
Definition = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


# 메인 파싱 함수
def parse_code(file: FileInfo) -> list[Chunk]:
    """코드 파일을 최상위 함수 / 클래스 단위 Chunk로 나눈다.

    Args:
        file: 경로와 document_id가 채워진 코드 FileInfo 입니다.

    Returns:
        파일에 나온 순서대로 정렬된 Chunk가 리턴되고 start_line / end_line은 1부터이고 끝 줄을 포함합니다.
        내용이 공백뿐이면 빈 리스트를 반환합니다.

    Raise:
        FileNotFoundError: file.path 에 파일이 없을 때.
        UnicodeDecodeError: UTF-8로 읽을 수 없는 파일일 때.
    """

    path = Path(file.path)

    if not path.is_file():
        raise FileNotFoundError(f"코드 파일을 찾을 수 없습니다: {file.path}")

    document_id = file.document_id or path.name
    lines = path.read_text(encoding="utf-8").splitlines()
    if trim_blank(lines, 1, len(lines)) is None:
        return []

    spans = ast_spans(lines)
    if spans is None:
        spans = window_spans(len(lines))

    return [
        make_chunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=slice_lines(lines, start_line, end_line),
            start_line=start_line,
            end_line=end_line,
        )
        for chunk_index, (start_line, end_line) in enumerate(spans)
    ]


# ------- 메인에서 쓰는 함수 정의!! ------------------------------------------


def trim_blank(lines: list[str], start_line: int, end_line: int) -> tuple[int, int] | None:
    """구간 앞뒤의 빈 줄을 잘라내고, 남는 코드가 없으면 None을 반환한다.

    Args:
        lines: 전체 소스 코드를 줄 단위로 나눈 리스트.
        start_line: 구간 시작 줄 번호 (1-based, 포함).
        end_line: 구간 끝 줄 번호 (1-based, 포함).

    Returns:
        빈 줄을 제외한 (start_line, end_line) 구간. 구간 전체가 빈 줄뿐이면 None.
    """

    while start_line <= end_line and not lines[start_line - 1].strip():
        start_line += 1
    while end_line >= start_line and not lines[end_line - 1].strip():
        end_line -= 1
    if start_line > end_line:
        return None
    return start_line, end_line


def ast_spans(lines: list[str]) -> list[tuple[int, int]] | None:
    """AST로 최상위 함수/클래스 구간과 그 사이 모듈 코드 구간을 찾는다.

    Args:
        lines: 전체 소스 코드를 줄 단위로 나눈 리스트.

    Returns:
        (start_line, end_line) 구간의 리스트. start_line / end_line은 1부터이고
        끝 줄을 포함한다. 파일에 나온 순서대로 정렬된다.
        문법 오류로 파싱에 실패하면 None.
    """
    try:
        module = ast.parse("\n".join(lines))
    except SyntaxError:
        return None

    definitions = sorted(
        definition_span(node) for node in module.body if isinstance(node, Definition)
    )

    return fill_gaps(definitions, lines)


def definition_span(node: Definition) -> tuple[int, int]:
    """데코레이터 첫 줄부터 정의 끝 줄까지 구간을 구한다.

    Args:
        node: 최상위 함수/클래스/비동기 함수 정의를 나타내는 AST 노드.

    Returns:
        (start_line, end_line) 구간. 데코레이터가 있으면 그 첫 줄부터,
        없으면 정의 자체의 시작 줄부터 시작한다. 1-based이고 끝 줄을 포함한다.
    """

    start_line = node.lineno
    if node.decorator_list:
        start_line = min(start_line, node.decorator_list[0].lineno)
    return start_line, node.end_lineno or node.lineno


def fill_gaps(definitions: list[tuple[int, int]], lines: list[str]) -> list[tuple[int, int]]:
    """정의 사이에 남은 모듈 수준 코드(import, 상수, __main__)도 구간으로 남긴다.

    Args:
        definitions: 최상위 함수/클래스 정의의 (start_line, end_line) 구간 리스트.
            파일에 나온 순서대로 정렬되어 있어야 한다.
        lines: 전체 소스 코드를 줄 단위로 나눈 리스트.

    Returns:
        정의 구간과 그 사이(또는 앞뒤)에 남은 모듈 수준 코드 구간을 모두 합쳐
        파일에 나온 순서대로 정렬한 (start_line, end_line) 리스트.
        빈 줄만 있는 구간은 제외된다.
    """
    spans: list[tuple[int, int]] = []
    cursor = 1

    for start_line, end_line in definitions:
        gap = trim_blank(lines, cursor, start_line - 1)
        if gap is not None:
            spans.append(gap)
        spans.append((start_line, end_line))
        cursor = end_line + 1

    tail = trim_blank(lines, cursor, len(lines))
    if tail is not None:
        spans.append(tail)
    return spans


def window_spans(total_lines: int) -> list[tuple[int, int]]:
    """AST 파싱 실패 시 쓰는 폴백 구간. 문법이 깨져도 줄 번호는 살려서 출처를 남긴다.

    Args:
        total_lines: 파일 전체 줄 수.

    Returns:
        (start_line, end_line) 구간의 리스트. 각 구간은 FALLBACK_WINDOW_LINES 크기이고,
        다음 구간은 FALLBACK_STRIDE_LINES만큼 이동해 시작하므로 경계 부근이 겹친다.
        1-based이고 끝 줄을 포함한다.
    """
    spans: list[tuple[int, int]] = []
    start_line = 1

    while start_line <= total_lines:
        end_line = min(start_line + FALLBACK_WINDOW_LINES - 1, total_lines)
        spans.append((start_line, end_line))
        if end_line == total_lines:
            break
        start_line += FALLBACK_STRIDE_LINES

    return spans


def make_chunk(
    *,
    document_id: str,
    chunk_index: int,
    content: str,
    start_line: int,
    end_line: int,
) -> Chunk:
    """구간 정보로부터 Chunk 객체를 만든다.

    Args:
        document_id: 이 청크가 속한 문서의 ID.
        chunk_index: 문서 내에서 이 청크의 순번 (0부터 시작).
        content: 이 구간에 해당하는 코드 텍스트.
        start_line: 구간 시작 줄 번호 (1-based, 포함).
        end_line: 구간 끝 줄 번호 (1-based, 포함).

    Returns:
        chunk_id, source_type 등 메타데이터가 채워진 Chunk 객체.
    """
    return Chunk(
        chunk_id=f"{document_id}:chunk:{chunk_index:04d}",
        document_id=document_id,
        source_type="code",
        content=content,
        chunk_index=chunk_index,
        start_line=start_line,
        end_line=end_line,
    )


def slice_lines(lines: list[str], start_line: int, end_line: int) -> str:
    """1-based, 끝 줄 포함 구간을 그대로 잘라낸다. 코드는 들여쓰기가 의미라 정제하지 않는다.

    Args:
        lines: 전체 소스 코드를 줄 단위로 나눈 리스트.
        start_line: 자를 구간의 시작 줄 번호 (1-based, 포함).
        end_line: 자를 구간의 끝 줄 번호 (1-based, 포함).

    Returns:
        start_line부터 end_line까지의 줄을 개행 문자로 이어붙인 문자열.
    """
    return "\n".join(lines[start_line - 1 : end_line])
