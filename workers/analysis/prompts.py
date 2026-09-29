"""
C — LangChain PromptTemplate 모음.

연동: concept.py, code_flow.py, flow_diagrams.py, reference_tables.py, cross_reference.py, practice_notes.py
강의: ChatGoogleGenerativeAI + PromptTemplate + structured output
"""

from __future__ import annotations

from langchain_core.prompts import PromptTemplate

_CONCEPT_TEMPLATE = """당신은 학습자를 위해 PDF 학습 자료에서 핵심 이론/개념을 요약하는 어시스턴트입니다.

아래는 PDF에서 추출된 청크들입니다. 각 청크는 `[chunk_id | page:N]` 헤더로 시작합니다.

{evidence}

지침:
- 위 내용을 근거로 핵심 개념을 식별하고, 개념마다 간결한 title과 이해하기 쉬운 summary를 작성하세요.
- 수식이 등장하면 formula 필드에 LaTeX 또는 읽을 수 있는 일반식으로 적고, 없으면 생략하세요.
- source_chunk_ids에는 반드시 위 헤더에 실제로 존재하는 chunk_id만 그대로 사용하세요. 존재하지 않는 chunk_id를 지어내지 마세요.
- concept_id는 "concept-001"처럼 순번으로 고유하게 부여하세요.
- 코드와 관련된 개념이면 related_code_refs에 관련 코드 단위 이름을 적고, 모르면 빈 리스트로 두세요.
"""

_CODE_FLOW_TEMPLATE = """당신은 파이썬 코드의 실행 순서와 데이터 흐름을 분석하는 어시스턴트입니다.

아래는 코드에서 추출된 청크들입니다. 각 청크는 `[chunk_id | line:START-END]` 헤더로 시작합니다.

{evidence}

지침:
- 코드 단위(함수/파일/레이어)별로 실행 순서와 데이터 변환 흐름을 execution_flow에 서술하세요.
- key_points에는 핵심 API 호출, 제어 흐름 분기, 중요 변수명 등을 짧은 문구로 나열하세요.
- unit_type은 함수 하나면 "function", 파일 전체 흐름이면 "file", 여러 파일에 걸친 구조면 "layer"로 판단하세요.
- source_chunk_ids에는 반드시 위 헤더에 실제로 존재하는 chunk_id만 그대로 사용하세요.
"""

_CROSS_REFERENCE_TEMPLATE = """당신은 학습 자료의 이론 설명과 실제 코드 구현을 서로 연결(Cross-Referencing)하는 어시스턴트입니다.

아래는 이미 추출된 개념 목록과 코드 단위 목록입니다.

[개념 목록]
{concepts}

[코드 단위 목록]
{code_units}

[원본 근거 청크]
{evidence}

지침:
- 개념과 코드가 서로 대응되면 ref_type="matched"로 두고 concept_ref(개념의 concept_id)와 code_ref(코드 단위의 unit_name)를 모두 채우세요.
- 대응되는 개념 없이 코드만 존재하면 ref_type="code_only", 대응되는 코드 없이 개념만 존재하면 ref_type="concept_only"로 표시하세요.
- explanation에는 "이 코드는 자료의 어떤 개념을 구현한 것인지"를 구체적으로 설명하세요.
- source_chunk_ids에는 매핑의 근거가 된 chunk_id를 [원본 근거 청크]에 실제로 존재하는 것만 사용하세요.
"""

_FLOW_DIAGRAM_TEMPLATE = """당신은 학습 자료와 코드에서 흐름도를 뽑아내는 어시스턴트입니다.

아래는 PDF와 코드에서 추출된 청크들입니다. 각 청크는 `[chunk_id | 위치]` 헤더로 시작합니다.

{evidence}

지침:
- scope 는 다음 기준으로 판단하세요.
  - pipeline: 시스템/데이터가 거쳐 가는 처리 단계 구조
  - curriculum_progression: 학습 자료가 제시하는 단계별 진행 순서
  - execution_trace: 코드나 에이전트가 실제로 실행되는 순서
- diagram 은 렌더링 없이 그대로 출력되는 일반 텍스트입니다. `A → B → C` 처럼 화살표로 표기하고,
  분기나 조건은 `(조건?)` 형태로 덧붙이세요. Mermaid 문법이나 코드 펜스는 쓰지 마세요.
- description 에는 그 흐름이 언제 끝나는지, 반복이 있다면 무엇이 반복을 멈추는지 적으세요.
- source_chunk_ids 에는 반드시 위 헤더에 실제로 존재하는 chunk_id만 그대로 사용하세요.
- 근거가 불충분하면 항목을 만들지 말고 비워 두세요.
"""

_REFERENCE_TABLE_TEMPLATE = """당신은 학습 자료를 비교·요약하는 참조표를 만드는 어시스턴트입니다.

아래는 PDF와 코드에서 추출된 청크들입니다. 각 청크는 `[chunk_id | 위치]` 헤더로 시작합니다.

{evidence}

지침:
- 나열된 항목들을 한눈에 비교할 수 있을 때만 표를 만드세요 (예: 단계별 학습 로드맵, API 비교).
- columns 에 열 제목을 넣고, rows 의 각 행은 columns 와 길이가 정확히 같아야 합니다.
- 셀 값은 한 줄로 짧게 쓰세요. 줄바꿈이 들어가면 표가 깨집니다.
- source_chunk_ids 에는 반드시 위 헤더에 실제로 존재하는 chunk_id만 그대로 사용하세요.
- 비교할 축이 없으면 표를 억지로 만들지 말고 비워 두세요.
"""


def concept_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(_CONCEPT_TEMPLATE)


def code_flow_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(_CODE_FLOW_TEMPLATE)


def flow_diagram_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(_FLOW_DIAGRAM_TEMPLATE)


def reference_table_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(_REFERENCE_TABLE_TEMPLATE)


def cross_reference_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(_CROSS_REFERENCE_TEMPLATE)


def practice_note_prompt() -> PromptTemplate:
    raise NotImplementedError("C: practice_note_prompt — WEAVE-22 범위 밖")
