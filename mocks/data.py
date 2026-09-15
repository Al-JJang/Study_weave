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
        document_id=f"{MOCK_REQUEST_ID}:langgraph_agent_guide.pdf",
        filename="langgraph_agent_guide.pdf",
        source_type="pdf",
        path="data/samples/langgraph_agent_guide.pdf",
    ),
    FileInfo(
        document_id=f"{MOCK_REQUEST_ID}:agentEx4.py",
        filename="agentEx4.py",
        source_type="code",
        path="data/samples/agentEx4.py",
    ),
]

MOCK_PARSED_CHUNKS = [
    Chunk(
        chunk_id=f"{MOCK_REQUEST_ID}:langgraph_agent_guide.pdf:chunk:0000",
        document_id=f"{MOCK_REQUEST_ID}:langgraph_agent_guide.pdf",
        source_type="pdf",
        content=(
            "LangChain 의 @tool 데코레이터는 일반 파이썬 함수를 LLM 이 호출 가능한 Tool 로 변환한다. "
            "함수의 docstring 이 곧 Tool Description 이 되며, LLM 은 이 설명만 보고 Tool 사용 여부를 "
            "판단하므로 목적뿐 아니라 언제 사용하면 안 되는지까지 docstring 에 적어야 오남용을 막을 수 있다."
        ),
        chunk_index=0,
        page_number=1,
    ),
    Chunk(
        chunk_id=f"{MOCK_REQUEST_ID}:langgraph_agent_guide.pdf:chunk:0001",
        document_id=f"{MOCK_REQUEST_ID}:langgraph_agent_guide.pdf",
        source_type="pdf",
        content=(
            "LangGraph 의 Agent Loop 는 START → agent → tools → agent → ... → END 구조로 동작한다. "
            "tools 노드(ToolNode)가 만든 실행 결과(ToolMessage)가 다시 agent 노드로 들어가면, "
            "LLM 은 충분한 정보가 모였는지 스스로 판단해 다음 Tool 호출 여부를 결정한다. "
            "무한 루프를 막기 위해 tool_rounds 같은 카운터와 MAX_TOOL_ROUNDS 상한을 함께 둔다."
        ),
        chunk_index=1,
        page_number=2,
    ),
    Chunk(
        chunk_id=f"{MOCK_REQUEST_ID}:agentEx4.py:chunk:0000",
        document_id=f"{MOCK_REQUEST_ID}:agentEx4.py",
        source_type="code",
        content=(
            "class AgentState(MessagesState):\n"
            "    tool_rounds: int\n\n"
            "def agent_node(state: AgentState) -> dict:\n"
            "    response = model_with_tools.invoke([SYSTEM_PROMPT, *state['messages']])\n"
            "    rounds = state['tool_rounds'] + (1 if response.tool_calls else 0)\n"
            "    return {'messages': [response], 'tool_rounds': rounds}\n\n"
            "def route_after_agent(state: AgentState) -> Literal['tools', 'end']:\n"
            "    last = state['messages'][-1]\n"
            "    if last.tool_calls and state['tool_rounds'] < MAX_TOOL_ROUNDS:\n"
            "        return 'tools'\n"
            "    return 'end'\n\n"
            "builder.add_conditional_edges('agent', route_after_agent, {'tools': 'tools', 'end': END})\n"
            "builder.add_edge('tools', 'agent')\n"
        ),
        chunk_index=0,
        start_line=1,
        end_line=24,
    ),
]

MOCK_RETRIEVED_CHUNKS = [
    RetrievedChunk(
        **MOCK_PARSED_CHUNKS[1].model_dump(),
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
        **MOCK_PARSED_CHUNKS[0].model_dump(),
        distance=0.27,
        vector_rank=3,
        retrieval_sources=["vector"],
    ),
]

MOCK_CONCEPTS = [
    ConceptItem(
        concept_id="concept-001",
        title="@tool 데코레이터와 Tool Description",
        summary=(
            "일반 파이썬 함수를 @tool 로 감싸면 LLM 이 호출 가능한 Tool 이 된다. "
            "함수의 docstring 이 그대로 Tool Description 으로 쓰이며, LLM 은 이 설명만 보고 "
            "Tool 사용 여부를 판단하므로 목적/사용 시점/사용하면 안 되는 경우까지 docstring 에 명시해야 한다."
        ),
        related_code_refs=["code-001"],
        source_chunk_ids=[MOCK_PARSED_CHUNKS[0].chunk_id],
    ),
    ConceptItem(
        concept_id="concept-002",
        title="Agent Loop (순차 Tool 호출) 패턴",
        summary=(
            "agent 와 tools 노드를 add_edge('tools', 'agent') 로 순환시켜, Tool 실행 결과를 "
            "다시 LLM 에게 보여주고 다음 행동을 스스로 판단하게 하는 구조다. "
            "tool_rounds 카운터와 MAX_TOOL_ROUNDS 상한으로 무한 루프를 방지한다."
        ),
        related_code_refs=["code-001"],
        source_chunk_ids=[MOCK_PARSED_CHUNKS[1].chunk_id],
    ),
]

MOCK_CODE_UNITS = [
    CodeAnalysisItem(
        unit_name="agentEx4.py",
        unit_type="file",
        execution_flow=(
            "agent_node 가 SystemPrompt 와 누적 messages 로 모델을 호출하고, tool_calls 유무에 따라 "
            "tool_rounds 를 갱신한다. route_after_agent 가 tool_calls 와 tool_rounds 를 보고 "
            "'tools' 또는 'end' 로 분기하며, add_edge('tools', 'agent') 로 순환 구조를 완성한다."
        ),
        key_points=["add_conditional_edges", "tool_rounds", "route_after_agent"],
        source_chunk_ids=[MOCK_PARSED_CHUNKS[2].chunk_id],
    ),
]

MOCK_FLOWS = [
    FlowDiagram(
        scope="execution_trace",
        title="Agent Loop 실행 흐름",
        diagram="START → agent → (tool_calls?) → tools → agent → ... → (no tool_calls) → END",
        description=(
            "tool_calls 가 사라지거나 tool_rounds 가 MAX_TOOL_ROUNDS 를 넘을 때까지 "
            "agent 와 tools 사이를 순환한다."
        ),
        source_chunk_ids=[MOCK_PARSED_CHUNKS[1].chunk_id],
    ),
    FlowDiagram(
        scope="curriculum_progression",
        title="agentEx 학습 진행 순서 (발췌)",
        diagram=(
            "agentEx1(Tool 기초) → agentEx2(Tool Calling 관찰) → "
            "agentEx3(ToolNode 단발 실행) → agentEx4(Agent Loop 표준화)"
        ),
        description=(
            "Tool 을 정의하고 LLM 이 고르는 것만 관찰하던 단계에서, ToolNode 로 1회 실행해보고, "
            "마지막으로 agent⇄tools 순환 루프를 완성하는 순서로 난이도가 올라간다."
        ),
        source_chunk_ids=[MOCK_PARSED_CHUNKS[0].chunk_id],
    ),
]

MOCK_TABLES = [
    ReferenceTable(
        title="agentEx 학습 로드맵 (발췌)",
        columns=["파일", "핵심 주제"],
        rows=[
            ["agentEx1", "Tool 기초 (@tool, args_schema)"],
            ["agentEx4", "Agent Loop (순차 Tool 호출)"],
        ],
        source_chunk_ids=[MOCK_PARSED_CHUNKS[0].chunk_id, MOCK_PARSED_CHUNKS[1].chunk_id],
    ),
]

MOCK_CROSS_REFERENCES = [
    CrossReferenceItem(
        ref_type="matched",
        code_ref="code-001",
        concept_ref="concept-002",
        explanation=(
            "교안의 Agent Loop 설명(agent→tools→agent 순환, tool_rounds 카운터)이 "
            "agentEx4.py 의 route_after_agent/add_conditional_edges/add_edge 구성과 그대로 대응한다."
        ),
        source_chunk_ids=[MOCK_PARSED_CHUNKS[1].chunk_id, MOCK_PARSED_CHUNKS[2].chunk_id],
    ),
]

MOCK_PRACTICE_NOTES = [
    PracticeNote(
        note_type="tip",
        scope="learner_pattern",
        content="Tool docstring 에는 '언제 쓰는지'뿐 아니라 '언제 쓰면 안 되는지'까지 적어야 LLM이 오남용하지 않는다",
        caution="docstring 이 부실하면 이름만 보고 잘못된 상황에서 Tool 을 호출할 수 있다.",
        source_chunk_ids=[MOCK_PARSED_CHUNKS[0].chunk_id],
    ),
    PracticeNote(
        note_type="checklist_item",
        scope="learner_pattern",
        content="tool_rounds/MAX_TOOL_ROUNDS 같은 무한 루프 방지 장치가 있는가?",
        source_chunk_ids=[MOCK_PARSED_CHUNKS[1].chunk_id],
    ),
]

MOCK_QUIZ_ITEMS = [
    QuizItem(
        quiz_type="mcq",
        question="LangGraph 에서 Tool 실행 결과(ToolMessage)를 만들고 agent 가 다시 판단하게 하는 노드는?",
        options=["MessagesState", "ToolNode", "RunnableBranch", "PersistentClient"],
        answer="ToolNode",
        explanation="ToolNode 가 tool_calls 를 실행해 ToolMessage 로 변환하면, agent 노드가 이를 보고 다음 행동을 판단한다.",
        source_chunk_ids=[MOCK_PARSED_CHUNKS[2].chunk_id],
    ),
    QuizItem(
        quiz_type="true_false",
        question="Tool 함수의 docstring 은 LLM 의 Tool 사용 여부 판단과 무관하다.",
        options=["True", "False"],
        answer="False",
        explanation="docstring 이 곧 Tool Description 이 되어 LLM 판단의 유일한 근거가 된다.",
        source_chunk_ids=[MOCK_PARSED_CHUNKS[0].chunk_id],
    ),
]

MOCK_MARKDOWN = """---
request_id: req-demo-001
route: both
tags: [studywave, langgraph, agent]
---

# 개념
- @tool 데코레이터는 일반 함수를 LLM이 호출 가능한 Tool로 바꾸며, docstring이 Tool Description이 된다.
- Agent Loop는 agent⇄tools 순환으로 Tool 실행 결과를 다시 LLM 판단에 넘긴다.

# 코드 분석
- agentEx4.py: agent_node/route_after_agent/add_conditional_edges로 Agent Loop를 구현한다.

# 흐름도
## Agent Loop 실행 흐름
START → agent → (tool_calls?) → tools → agent → ... → (no tool_calls) → END
tool_calls가 사라지거나 tool_rounds가 MAX_TOOL_ROUNDS를 넘을 때까지 agent와 tools 사이를 순환한다.

## agentEx 학습 진행 순서 (발췌)
agentEx1(Tool 기초) → agentEx2(Tool Calling 관찰) → agentEx3(ToolNode 단발 실행) → agentEx4(Agent Loop 표준화)

# 참조표
## agentEx 학습 로드맵 (발췌)
| 파일 | 핵심 주제 |
| --- | --- |
| agentEx1 | Tool 기초 (@tool, args_schema) |
| agentEx4 | Agent Loop (순차 Tool 호출) |

# 이론-코드 연결
- 교안의 Agent Loop 설명 ↔ agentEx4.py의 route_after_agent/add_conditional_edges/add_edge 구성

# 실무 노트
- [tip] Tool docstring에는 '언제 쓰는지'뿐 아니라 '언제 쓰면 안 되는지'까지 적어야 한다
  참고: docstring이 부실하면 이름만 보고 잘못된 상황에서 Tool을 호출할 수 있다.
- [checklist_item] tool_rounds/MAX_TOOL_ROUNDS 같은 무한 루프 방지 장치가 있는가?

# Quiz
1. LangGraph에서 Tool 실행 결과(ToolMessage)를 만들고 agent가 다시 판단하게 하는 노드는? 정답: ToolNode
2. Tool 함수의 docstring은 LLM의 Tool 사용 여부 판단과 무관하다. 정답: False
"""
