"""
workers/formatter/markdown.py 검증 테스트.

확인 항목:
1. 개념, 코드 분석, 흐름도, 참조표가 Markdown으로 변환되는지 확인
2. 참조표 셀 내부의 파이프 문자가 이스케이프되는지 확인
3. concept_ref가 concept_id에 대응하는 개념 제목으로 표시되는지 확인
4. Practice Notes가 Markdown으로 변환되는지 확인
5. MCQ, 단답형, True/False 퀴즈가 유형에 맞게 출력되는지 확인
6. 정답과 해설이 details 태그 내부에 포함되는지 확인
7. EMPTY_SECTION_POLICY에 따라 빈 섹션이 처리되는지 확인
8. 최종 Markdown 섹션 순서가 유지되는지 확인
9. YAML Front Matter에 request_id와 route가 포함되는지 확인
10. YAML 값의 특수문자가 안전하게 처리되는지 확인
11. source_chunk_ids가 NOTE callout으로 표시되는지 확인
12. 확인 필요 및 주의사항이 WARNING callout으로 표시되는지 확인
"""

from __future__ import annotations

import config
from schemas.analysis import (
    CodeAnalysisItem,
    ConceptItem,
    CrossReferenceItem,
    FlowDiagram,
    PracticeNote,
    ReferenceTable,
)
from schemas.quiz import QuizItem
from schemas.state import AgentState
from workers.formatter.markdown import format_markdown


def _make_sample_state() -> AgentState:
    """Markdown formatter 테스트용 AgentState를 생성합니다.

    Returns:
        C 분석 결과와 QuizItem이 포함된 테스트용 AgentState.
    """

    return {
        "concepts": [
            ConceptItem(
                concept_id="concept-langgraph",
                title="LangGraph",
                summary="LangGraph는 상태 기반 그래프 실행 흐름을 구성합니다.",
                formula="y = x + 1",
                needs_verification=True,
                related_code_refs=[
                    "router_node",
                ],
                source_chunk_ids=[
                    "chunk-001",
                ],
            )
        ],
        "code_units": [
            CodeAnalysisItem(
                unit_name="router_node",
                unit_type="function",
                execution_flow="현재 상태를 확인한 뒤 다음 실행 노드를 결정합니다.",
                key_points=[
                    "상태를 기반으로 분기합니다.",
                    "다음 노드를 결정합니다.",
                ],
                source_chunk_ids=[
                    "chunk-002",
                ],
            )
        ],
        "flows": [
            FlowDiagram(
                scope="execution_trace",
                title="Agent 실행 흐름",
                diagram="START → router → worker → END",
                description="Router가 실행할 Worker를 결정합니다.",
                needs_verification=False,
                source_chunk_ids=[
                    "chunk-003",
                ],
            )
        ],
        "tables": [
            ReferenceTable(
                title="구성요소 비교",
                columns=[
                    "구성요소",
                    "역할",
                ],
                rows=[
                    [
                        "Router",
                        "다음 노드 결정",
                    ],
                    [
                        "Worker",
                        "작업 수행 | 결과 반환",
                    ],
                ],
                source_chunk_ids=[
                    "chunk-004",
                ],
            )
        ],
        "cross_references": [
            CrossReferenceItem(
                ref_type="matched",
                code_ref="router_node",
                concept_ref="concept-langgraph",
                explanation="LangGraph의 라우팅 개념이 router_node 함수로 구현됩니다.",
                source_chunk_ids=[
                    "chunk-001",
                    "chunk-002",
                ],
            )
        ],
        "practice_notes": [
            PracticeNote(
                note_type="mistake",
                scope="learner_pattern",
                content="Router와 Worker의 역할을 혼동할 수 있습니다.",
                caution="Router는 작업을 직접 수행하지 않습니다.",
                source_chunk_ids=[
                    "chunk-002",
                ],
            )
        ],
        "quiz_items": [
            QuizItem(
                quiz_type="mcq",
                question="LangGraph에서 실행 흐름을 정의하는 객체는?",
                options=[
                    "StateGraph",
                    "ToolNode",
                    "Document",
                    "PromptTemplate",
                ],
                answer="StateGraph",
                explanation="StateGraph는 노드와 엣지를 사용해 실행 흐름을 정의합니다.",
                source_chunk_ids=[
                    "chunk-001",
                ],
            ),
            QuizItem(
                quiz_type="short",
                question="다음 실행 노드를 결정하는 역할은?",
                answer="Router",
                explanation="Router는 현재 상태를 기반으로 다음 실행 대상을 결정합니다.",
                source_chunk_ids=[
                    "chunk-002",
                ],
            ),
            QuizItem(
                quiz_type="true_false",
                question="StateGraph는 실행 흐름을 정의할 수 있다.",
                answer="True",
                explanation="StateGraph는 그래프 실행 흐름을 정의합니다.",
                source_chunk_ids=[
                    "chunk-001",
                ],
            ),
        ],
    }


def test_format_markdown_contains_analysis_sections() -> None:
    """C 분석 결과가 각 Markdown 섹션에 포함되는지 확인합니다."""

    markdown = format_markdown(_make_sample_state())

    assert "## 개념 정리" in markdown
    assert "### LangGraph" in markdown
    assert "y = x + 1" in markdown

    assert "## 코드 분석" in markdown
    assert "### `router_node`" in markdown

    assert "## 흐름도" in markdown
    assert "Agent 실행 흐름" in markdown
    assert "`execution_trace`" in markdown
    assert "START → router → worker → END" in markdown

    assert "## 참조표" in markdown
    assert "| 구성요소 | 역할 |" in markdown


def test_format_markdown_escapes_table_pipe_character() -> None:
    """참조표 셀 내부의 파이프 문자가 이스케이프되는지 확인합니다."""

    markdown = format_markdown(_make_sample_state())

    assert "작업 수행 \\| 결과 반환" in markdown


def test_format_markdown_resolves_concept_reference_title() -> None:
    """concept_ref가 실제 concept_id의 제목으로 표시되는지 확인합니다."""

    markdown = format_markdown(_make_sample_state())

    assert "## 이론-코드 연결" in markdown
    assert "LangGraph (`concept-langgraph`)" in markdown
    assert "`router_node`" in markdown


def test_format_markdown_contains_practice_notes() -> None:
    """Practice Notes 내용과 주의사항이 출력되는지 확인합니다."""

    markdown = format_markdown(_make_sample_state())

    assert "## Practice Notes" in markdown
    assert "Router와 Worker의 역할을 혼동할 수 있습니다." in markdown
    assert "Router는 작업을 직접 수행하지 않습니다." in markdown


def test_format_markdown_formats_quiz_types() -> None:
    """객관식, 단답형, True/False 퀴즈가 유형에 맞게 출력되는지 확인합니다."""

    markdown = format_markdown(_make_sample_state())

    assert "## Quiz" in markdown

    assert "A. StateGraph" in markdown
    assert "B. ToolNode" in markdown
    assert "C. Document" in markdown
    assert "D. PromptTemplate" in markdown

    assert "다음 실행 노드를 결정하는 역할은?" in markdown

    assert "StateGraph는 실행 흐름을 정의할 수 있다." in markdown
    assert "- True" in markdown
    assert "- False" in markdown


def test_format_markdown_hides_quiz_answer_in_details() -> None:
    """퀴즈 정답과 해설이 details 태그 내부에 포함되는지 확인합니다."""

    markdown = format_markdown(_make_sample_state())

    assert "<details>" in markdown
    assert "<summary>정답 및 해설</summary>" in markdown
    assert "**정답:** StateGraph" in markdown
    assert "</details>" in markdown


def test_format_markdown_omits_empty_sections(
    monkeypatch,
) -> None:
    """EMPTY_SECTION_POLICY가 omit이면 빈 섹션을 생략합니다."""

    monkeypatch.setattr(
        config,
        "EMPTY_SECTION_POLICY",
        "omit",
    )

    state: AgentState = {
        "concepts": [],
        "code_units": [],
        "flows": [],
        "tables": [],
        "cross_references": [],
        "practice_notes": [],
        "quiz_items": [],
    }

    markdown = format_markdown(state)

    assert markdown == "---\n---\n"
    assert "## 개념 정리" not in markdown
    assert "## 코드 분석" not in markdown
    assert "## Quiz" not in markdown


def test_format_markdown_uses_placeholder_for_empty_sections(
    monkeypatch,
) -> None:
    """EMPTY_SECTION_POLICY가 placeholder이면 빈 섹션 안내를 출력합니다."""

    monkeypatch.setattr(
        config,
        "EMPTY_SECTION_POLICY",
        "placeholder",
    )

    state: AgentState = {
        "concepts": [],
        "code_units": [],
        "flows": [],
        "tables": [],
        "cross_references": [],
        "practice_notes": [],
        "quiz_items": [],
    }

    markdown = format_markdown(state)

    assert "## 개념 정리" in markdown
    assert "## 코드 분석" in markdown
    assert "## Quiz" in markdown
    assert "_표시할 내용이 없습니다._" in markdown


def test_format_markdown_keeps_section_order() -> None:
    """최종 Markdown의 섹션 순서가 정의된 목차와 일치하는지 확인합니다."""

    markdown = format_markdown(_make_sample_state())

    expected_sections = [
        "## 개념 정리",
        "## 코드 분석",
        "## 흐름도",
        "## 참조표",
        "## 이론-코드 연결",
        "## Practice Notes",
        "## Quiz",
    ]

    positions = [markdown.index(section) for section in expected_sections]

    assert positions == sorted(positions)


def test_format_markdown_contains_yaml_front_matter() -> None:
    """request_id와 route가 YAML Front Matter에 포함되는지 확인합니다."""

    state = _make_sample_state()
    state["request_id"] = "req-001"
    state["route"] = "both"

    markdown = format_markdown(state)

    assert markdown.startswith("---\n")
    assert 'request_id: "req-001"' in markdown
    assert 'route: "both"' in markdown


def test_format_markdown_escapes_yaml_value() -> None:
    """YAML 값의 따옴표 등 특수문자가 안전하게 처리되는지 확인합니다."""

    state = _make_sample_state()
    state["request_id"] = 'req-"001"'

    markdown = format_markdown(state)

    assert 'request_id: "req-\\"001\\""' in markdown


def test_format_markdown_uses_source_chunk_callout() -> None:
    """근거 Chunk가 NOTE callout으로 출력되는지 확인합니다."""

    markdown = format_markdown(_make_sample_state())

    assert "> [!NOTE] 근거 Chunk" in markdown
    assert "> chunk-001" in markdown


def test_format_markdown_uses_warning_callout() -> None:
    """확인 필요와 주의 문구가 WARNING callout으로 출력되는지 확인합니다."""

    markdown = format_markdown(_make_sample_state())

    assert "> [!WARNING] 확인 필요" in markdown
    assert "> [!WARNING] 주의" in markdown
