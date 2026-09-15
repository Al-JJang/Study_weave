"""
병렬 개발용 Mock. B→C, C→D 가 서로 완성될 때까지 기다리지 않아도 된다.

연동: graph/supervisor.py (USE_MOCK=True)
"""

from __future__ import annotations

from schemas.analysis import (
    CodeAnalysisItem,
    ConceptItem,
    CrossReferenceItem,
    FlowDiagram,
    PracticeNote,
    ReferenceTable,
)
from schemas.files import Chunk, FileInfo, RetrievedChunk
from schemas.quiz import QuizItem

MOCK_REQUEST_ID = "req-demo-001"

MOCK_FILES = [
    FileInfo(
        document_id=f"{MOCK_REQUEST_ID}:langgraph.pdf",
        filename="langgraph.pdf",
        source_type="pdf",
        path="data/samples/langgraph.pdf",
    ),
    FileInfo(
        document_id=f"{MOCK_REQUEST_ID}:graph_demo.py",
        filename="graph_demo.py",
        source_type="code",
        path="data/samples/graph_demo.py",
    ),
]

MOCK_PARSED_CHUNKS = [
    Chunk(
        chunk_id=f"{MOCK_REQUEST_ID}:langgraph.pdf:chunk:0000",
        document_id=f"{MOCK_REQUEST_ID}:langgraph.pdf",
        source_type="pdf",
        content=(
            "LangGraph 의 StateGraph 는 Node 와 Edge 로 실행 순서를 정의한다. "
            "START 에서 시작해 add_node / add_edge 로 연결한 뒤 compile() 한다. "
            "각 Node 는 State 에서 자신이 만든 key 만 반환하는 것이 안전하다."
        ),
        chunk_index=0,
        page_number=1,
    ),
    Chunk(
        chunk_id=f"{MOCK_REQUEST_ID}:langgraph.pdf:chunk:0001",
        document_id=f"{MOCK_REQUEST_ID}:langgraph.pdf",
        source_type="pdf",
        content=(
            "pgvector 는 PostgreSQL 에 임베딩을 저장한다. "
            "검색 시 request_id / document_id 필터를 걸면 다른 자료가 섞이지 않는다. "
            "distance 가 작을수록 질문과 가깝다."
        ),
        chunk_index=1,
        page_number=2,
    ),
    Chunk(
        chunk_id=f"{MOCK_REQUEST_ID}:graph_demo.py:chunk:0000",
        document_id=f"{MOCK_REQUEST_ID}:graph_demo.py",
        source_type="code",
        content=(
            "builder = StateGraph(AgentState)\n"
            "builder.add_node('parse', parse_files_node)\n"
            "builder.add_edge(START, 'route')\n"
            "graph = builder.compile()\n"
        ),
        chunk_index=0,
        start_line=10,
        end_line=14,
    ),
]

MOCK_RETRIEVED_CHUNKS = [
    RetrievedChunk(
        **MOCK_PARSED_CHUNKS[0].model_dump(),
        distance=0.12,
        vector_rank=1,
        retrieval_sources=["vector"],
    ),
    RetrievedChunk(
        **MOCK_PARSED_CHUNKS[2].model_dump(),
        distance=0.18,
        vector_rank=2,
        retrieval_sources=["vector"],
    ),
    RetrievedChunk(
        **MOCK_PARSED_CHUNKS[1].model_dump(),
        distance=0.27,
        vector_rank=3,
        retrieval_sources=["vector"],
    ),
]

MOCK_CONCEPTS = [
    ConceptItem(
        concept_id="concept-001",
        title="StateGraph 실행 모델",
        summary=(
            "Node 를 등록하고 Edge 로 순서를 정한 뒤 compile 하면 "
            "START → Node → END 로 State 가 흐른다."
        ),
        related_code_refs=["code-001"],
        source_chunk_ids=[MOCK_PARSED_CHUNKS[0].chunk_id],
    ),
]

MOCK_CODE_UNITS = [
    CodeAnalysisItem(
        unit_name="code-001",
        unit_type="file",
        execution_flow=(
            "add_node 로 parse 를 붙이고 START 에서 route 로 보낸 뒤 compile 한다. "
            "실제 분기 조건은 add_conditional_edges 에서 구현한다."
        ),
        key_points=["add_node", "add_edge", "compile"],
        source_chunk_ids=[MOCK_PARSED_CHUNKS[2].chunk_id],
    ),
]

MOCK_FLOWS = [
    FlowDiagram(
        scope="pipeline",
        title="StudyWave 파이프라인 흐름",
        diagram="route → parse → retrieve → analyze → format → verify",
        description="AgentState 가 6개 Node 를 순서대로 통과하며 채워진다.",
        source_chunk_ids=[MOCK_PARSED_CHUNKS[0].chunk_id],
    ),
]

MOCK_TABLES = [
    ReferenceTable(
        title="Node 별 반환 key",
        columns=["Node", "반환 key"],
        rows=[
            ["parse", "files, parsed_chunks"],
            ["retrieve", "retrieved_chunks"],
        ],
        source_chunk_ids=[MOCK_PARSED_CHUNKS[0].chunk_id],
    ),
]

MOCK_CROSS_REFERENCES = [
    CrossReferenceItem(
        ref_type="matched",
        code_ref="code-001",
        concept_ref="concept-001",
        explanation="교안 p.1 의 StateGraph 설명을 graph_demo.py 10-14행이 그대로 구현한다.",
        source_chunk_ids=[MOCK_PARSED_CHUNKS[0].chunk_id, MOCK_PARSED_CHUNKS[2].chunk_id],
    ),
]

MOCK_PRACTICE_NOTES = [
    PracticeNote(
        note_type="mistake",
        scope="learner_pattern",
        content="검색 결과에 다른 주차 자료가 섞인다",
        caution="pgvector WHERE 절에 request_id/document_id 필터를 걸지 않으면 발생한다.",
        source_chunk_ids=[MOCK_PARSED_CHUNKS[1].chunk_id],
    ),
]

MOCK_QUIZ_ITEMS = [
    QuizItem(
        quiz_type="mcq",
        question="LangGraph 에서 실행 순서를 정의하는 객체는?",
        options=["MessagesState", "StateGraph", "ToolNode", "PersistentClient"],
        answer="StateGraph",
        explanation="교안: StateGraph 가 Node/Edge 로 순서를 정의하고 compile 한다.",
        source_chunk_ids=[MOCK_PARSED_CHUNKS[0].chunk_id],
    ),
    QuizItem(
        quiz_type="true_false",
        question="벡터 검색에서 distance 가 클수록 질문과 더 가깝다.",
        options=["True", "False"],
        answer="False",
        explanation="distance 가 작을수록 가깝다.",
        source_chunk_ids=[MOCK_PARSED_CHUNKS[1].chunk_id],
    ),
]

MOCK_MARKDOWN = """---
request_id: req-demo-001
route: both
tags: [studywave, langgraph]
---

# 개념
- StateGraph 는 Node/Edge 로 실행 순서를 정의한다.

# 코드 분석
- graph_demo.py 10-14행이 StateGraph 뼈대다.

# 이론-코드 연결
- 교안 p.1 ↔ graph_demo.py 10-14행

# Troubleshooting
- 자료 혼입: request_id 필터 누락

# Quiz
1. LangGraph 에서 실행 순서를 정의하는 객체는? 정답: StateGraph
"""
