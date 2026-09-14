"""B — PDF 파서.

PyPDF/pdfplumber로 목차와 페이지 번호가 붙은 본문을 Chunk로 만든다.
Graph Node(`parse_files_node`)는 아직 이 함수만 호출하면 된다.
"""

from __future__ import annotations

from pathlib import Path

import pdfplumber
from pypdf import PdfReader
from pypdf.generic import Destination

from schemas.files import Chunk, FileInfo


def parse_pdf(file: FileInfo) -> list[Chunk]:
    """PDF에서 목차와 페이지 단위 본문을 추출한다.

    Args:
        file: 경로와 document_id가 채워진 PDF FileInfo.

    Returns:
        목차 Chunk(있으면) 다음에 페이지 Chunk. page_number는 1부터.

    Raises:
        FileNotFoundError: file.path 에 PDF가 없을 때.
        ValueError: PDF가 아니거나 페이지를 하나도 읽지 못했을 때.
    """
    path = Path(file.path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF를 찾을 수 없습니다: {file.path}")

    document_id = file.document_id or path.name
    chunks: list[Chunk] = []
    index = 0

    toc_text = _extract_toc(path)
    if toc_text:
        chunks.append(
            _make_chunk(
                document_id=document_id,
                chunk_index=index,
                content=toc_text,
                page_number=1,
            )
        )
        index += 1

    pages = _extract_pages(path)
    if not pages:
        raise ValueError(f"페이지 텍스트를 추출하지 못했습니다: {file.path}")

    for page_number, text in pages:
        chunks.append(
            _make_chunk(
                document_id=document_id,
                chunk_index=index,
                content=text,
                page_number=page_number,
            )
        )
        index += 1

    return chunks


def _make_chunk(
    *,
    document_id: str,
    chunk_index: int,
    content: str,
    page_number: int,
) -> Chunk:
    return Chunk(
        chunk_id=f"{document_id}:chunk:{chunk_index:04d}",
        document_id=document_id,
        source_type="pdf",
        content=content,
        chunk_index=chunk_index,
        page_number=page_number,
    )


def _clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _extract_pages(path: Path) -> list[tuple[int, str]]:
    """페이지 번호(1-based)와 본문 쌍. pdfplumber를 쓰고, 실패하면 pypdf."""
    pages = _extract_pages_pdfplumber(path)
    if pages:
        return pages
    return _extract_pages_pypdf(path)


def _extract_pages_pdfplumber(path: Path) -> list[tuple[int, str]]:
    extracted: list[tuple[int, str]] = []
    try:
        with pdfplumber.open(path) as pdf:
            for offset, page in enumerate(pdf.pages):
                raw = page.extract_text() or ""
                text = _clean_text(raw)
                if text:
                    extracted.append((offset + 1, text))
    except Exception:
        return []
    return extracted


def _extract_pages_pypdf(path: Path) -> list[tuple[int, str]]:
    extracted: list[tuple[int, str]] = []
    reader = PdfReader(str(path))
    for offset, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        text = _clean_text(raw)
        if text:
            extracted.append((offset + 1, text))
    return extracted


def _extract_toc(path: Path) -> str | None:
    """PDF outline(북마크)을 목차 문자열로 만든다. 없으면 None."""
    try:
        reader = PdfReader(str(path))
    except Exception:
        return None

    outlines = getattr(reader, "outline", None) or []
    if not outlines:
        return None

    lines: list[str] = []
    _flatten_outline(outlines, reader, lines, depth=0)
    if not lines:
        return None
    return "[목차]\n" + "\n".join(lines)


def _flatten_outline(
    items: list[object],
    reader: PdfReader,
    lines: list[str],
    depth: int,
) -> None:
    for item in items:
        if isinstance(item, list):
            _flatten_outline(item, reader, lines, depth + 1)
            continue
        title = _outline_title(item)
        if not title:
            continue
        page_number = _outline_page_number(reader, item)
        indent = "  " * depth
        if page_number is None:
            lines.append(f"{indent}{title}")
        else:
            lines.append(f"{indent}{title} (p.{page_number})")


def _outline_title(item: object) -> str:
    if isinstance(item, Destination):
        title = item.title
        return str(title).strip() if title else ""
    title = getattr(item, "title", None)
    return str(title).strip() if title else ""


def _outline_page_number(reader: PdfReader, item: object) -> int | None:
    try:
        number = reader.get_destination_page_number(item)  # type: ignore[arg-type]
    except Exception:
        return None
    if number is None:
        return None
    return int(number) + 1
