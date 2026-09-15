"""
workers/formatter/quiz.py 검증 테스트.

확인 항목:
1. Pydantic 모델과 dict가 JSON 직렬화 가능한 dict 목록으로 변환되는지 확인
2. C 최종 출력 스키마가 퀴즈 생성 근거에 정상적으로 포함되는지 확인
3. 누락된 C 분석 결과가 빈 리스트로 처리되는지 확인
4. C 분석 결과의 source_chunk_ids가 중복 없이 수집되는지 확인
5. 퀴즈 생성 프롬프트에 근거와 퀴즈 유형 생성 규칙이 포함되는지 확인
6. C 분석 결과가 없으면 퀴즈 생성을 거부
7. source_chunk_ids가 없으면 퀴즈 생성을 거부
8. 객관식과 단답형이 모두 포함된 결과를 허용
9. 객관식만 또는 단답형만 있는 결과를 거부
10. true_false는 선택적으로 추가할 수 있음
11. true_false 문항이 ["True", "False"] 선택지를 사용하는지 확인
12. Gemini Structured Output 결과가 list[QuizItem]으로 반환되는지 확인
13. 허용되지 않은 source_chunk_id가 포함된 퀴즈를 거부
"""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

import workers.formatter.quiz as quiz_module
from schemas.quiz import QuizItem
from workers.formatter.quiz import (
    QuizLLMOutput,
    _build_quiz_evidence,
    _build_quiz_prompt,
    _collect_source_chunk_ids,
    _serialize_items,
    produce_quiz_items,
)


def _make_valid_quiz_items() -> list[QuizItem]:
    """객관식과 단답형이 포함된 테스트용 퀴즈 목록을 생성합니다.

    Returns:
        객관식과 단답형이 혼합된 QuizItem 목록.
    """

    return [
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
            explanation=("StateGraph는 노드와 엣지를 사용해 그래프 실행 흐름을 정의합니다."),
            source_chunk_ids=[
                "chunk-001",
            ],
        ),
        QuizItem(
            quiz_type="short",
            question="다음 실행 노드를 결정하는 역할은?",
            answer="Router",
            explanation=("Router는 현재 상태를 기반으로 다음 실행 대상을 결정합니다."),
            source_chunk_ids=[
                "chunk-002",
            ],
        ),
    ]


def _make_sample_state() -> dict:
    """C 최종 출력 스키마를 반영한 테스트용 State를 생성합니다.

    Returns:
        D 퀴즈 생성 테스트에 사용할 State 딕셔너리.
    """

    return {
        "concepts": [
            {
                "concept_id": "concept-langgraph",
                "title": "LangGraph",
                "summary": ("LangGraph는 상태 기반 그래프 흐름을 구성합니다."),
                "formula": None,
                "needs_verification": False,
                "related_code_refs": [
                    "router_node",
                ],
                "source_chunk_ids": [
                    "chunk-001",
                ],
            }
        ],
        "code_units": [
            {
                "unit_name": "router_node",
                "unit_type": "function",
                "execution_flow": ("상태를 확인한 뒤 다음 실행 노드를 결정합니다."),
                "key_points": [
                    "라우팅 결과에 따라 다음 노드가 결정됩니다.",
                ],
                "source_chunk_ids": [
                    "chunk-002",
                ],
            }
        ],
        "flows": [
            {
                "scope": "execution_trace",
                "title": "Agent 실행 흐름",
                "diagram": "START → router → worker → END",
                "description": ("Router가 실행할 Worker를 결정합니다."),
                "needs_verification": False,
                "source_chunk_ids": [
                    "chunk-003",
                ],
            }
        ],
        "tables": [],
        "cross_references": [
            {
                "ref_type": "matched",
                "code_ref": "router_node",
                "concept_ref": "LangGraph Router",
                "explanation": ("Router 개념이 router_node 함수로 구현됩니다."),
                "source_chunk_ids": [
                    "chunk-001",
                    "chunk-002",
                ],
            }
        ],
        "practice_notes": [
            {
                "note_type": "mistake",
                "scope": "learner_pattern",
                "content": ("Router와 실제 Worker 실행 역할을 혼동할 수 있습니다."),
                "caution": ("Router는 다음 실행 대상을 결정하는 역할입니다."),
                "source_chunk_ids": [
                    "chunk-002",
                ],
            }
        ],
    }


def test_serialize_items_converts_pydantic_model_to_dict() -> None:
    """Pydantic 모델이 dict로 변환되는지 확인합니다."""

    quiz = QuizItem(
        quiz_type="short",
        question="LangGraph에서 실행 흐름을 정의하는 것은?",
        answer="그래프",
        explanation=("노드와 엣지를 통해 실행 흐름을 정의합니다."),
        source_chunk_ids=[
            "chunk-001",
        ],
    )

    result = _serialize_items(
        [
            quiz,
            {
                "chunk_id": "chunk-002",
            },
        ]
    )

    assert isinstance(
        result[0],
        dict,
    )

    assert result[0]["question"] == quiz.question

    assert result[1] == {
        "chunk_id": "chunk-002",
    }


def test_build_quiz_evidence_uses_c_output_schema() -> None:
    """C 최종 출력 필드가 evidence에 포함되는지 확인합니다."""

    state = _make_sample_state()

    evidence = _build_quiz_evidence(state)

    assert set(evidence.keys()) == {
        "concepts",
        "code_units",
        "flows",
        "tables",
        "cross_references",
        "practice_notes",
    }

    assert evidence["concepts"]
    assert evidence["code_units"]
    assert evidence["flows"]
    assert evidence["cross_references"]
    assert evidence["practice_notes"]

    assert evidence["tables"] == []


def test_build_quiz_evidence_uses_empty_lists_for_missing_data() -> None:
    """State에 없는 C 분석 결과가 빈 리스트로 처리되는지 확인합니다."""

    evidence = _build_quiz_evidence({})

    assert all(value == [] for value in evidence.values())


def test_collect_source_chunk_ids_removes_duplicates() -> None:
    """C 분석 결과의 source_chunk_ids가 중복 없이 수집되는지 확인합니다."""

    evidence = _build_quiz_evidence(_make_sample_state())

    source_chunk_ids = _collect_source_chunk_ids(evidence)

    assert source_chunk_ids == [
        "chunk-001",
        "chunk-002",
        "chunk-003",
    ]


def test_build_quiz_prompt_contains_evidence_and_rules() -> None:
    """프롬프트에 학습 근거와 퀴즈 생성 규칙이 포함되는지 확인합니다."""

    evidence = _build_quiz_evidence(_make_sample_state())

    source_chunk_ids = _collect_source_chunk_ids(evidence)

    prompt = _build_quiz_prompt(
        evidence,
        source_chunk_ids,
    )

    assert "concepts" in prompt
    assert "code_units" in prompt
    assert "flows" in prompt
    assert "cross_references" in prompt
    assert "practice_notes" in prompt

    assert "chunk-001" in prompt
    assert "chunk-002" in prompt
    assert "chunk-003" in prompt

    assert "객관식(mcq)" in prompt
    assert "단답형(short)" in prompt
    assert "반드시 모두 포함" in prompt

    assert "true_false 유형은 필요한 경우" in prompt
    assert "선택적으로 추가할 수 있습니다" in prompt
    assert 'answer는 "True" 또는 "False"' in prompt
    assert 'options는 반드시 ["True", "False"]' in prompt
    assert "source_chunk_ids" in prompt


def test_produce_quiz_items_rejects_empty_analysis() -> None:
    """C 분석 결과가 없으면 퀴즈 생성을 거부하는지 확인합니다."""

    state = {
        "concepts": [],
        "code_units": [],
        "flows": [],
        "tables": [],
        "cross_references": [],
        "practice_notes": [],
    }

    with pytest.raises(
        ValueError,
        match="C 분석 결과가 없습니다",
    ):
        produce_quiz_items(state)


def test_produce_quiz_items_rejects_missing_source_chunk_ids() -> None:
    """C 분석 결과에 출처 Chunk ID가 없으면 퀴즈 생성을 거부하는지 확인합니다."""

    state = {
        "concepts": [
            {
                "concept_id": "concept-langgraph",
                "title": "LangGraph",
                "summary": "상태 기반 그래프를 구성합니다.",
                "source_chunk_ids": [],
            }
        ],
        "code_units": [],
        "flows": [],
        "tables": [],
        "cross_references": [],
        "practice_notes": [],
    }

    with pytest.raises(
        ValueError,
        match="source_chunk_ids가 없습니다",
    ):
        produce_quiz_items(state)


def test_quiz_llm_output_accepts_mcq_and_short_mix() -> None:
    """객관식과 단답형이 모두 포함된 결과를 허용하는지 확인합니다."""

    quiz_items = _make_valid_quiz_items()

    result = QuizLLMOutput(quiz_items=quiz_items)

    quiz_types = {item.quiz_type for item in result.quiz_items}

    assert quiz_types == {
        "mcq",
        "short",
    }


def test_quiz_llm_output_rejects_only_short_quizzes() -> None:
    """단답형만 포함된 결과를 거부하는지 확인합니다."""

    quiz_items = [
        QuizItem(
            quiz_type="short",
            question="Router의 역할은?",
            answer="다음 실행 대상을 결정하는 것",
            explanation=("Router는 현재 상태를 보고 다음 실행 대상을 결정합니다."),
            source_chunk_ids=[
                "chunk-001",
            ],
        ),
        QuizItem(
            quiz_type="short",
            question="StateGraph의 역할은?",
            answer="그래프 실행 흐름 정의",
            explanation=("StateGraph는 노드와 엣지를 통해 실행 흐름을 정의합니다."),
            source_chunk_ids=[
                "chunk-002",
            ],
        ),
    ]

    with pytest.raises(
        ValidationError,
        match="객관식",
    ):
        QuizLLMOutput(quiz_items=quiz_items)


def test_quiz_llm_output_rejects_only_mcq_quizzes() -> None:
    """객관식만 포함된 결과를 거부하는지 확인합니다."""

    quiz_items = [
        QuizItem(
            quiz_type="mcq",
            question="LangGraph의 그래프 객체는?",
            options=[
                "StateGraph",
                "ToolNode",
                "Document",
                "PromptTemplate",
            ],
            answer="StateGraph",
            explanation=("StateGraph는 LangGraph의 실행 그래프를 정의합니다."),
            source_chunk_ids=[
                "chunk-001",
            ],
        ),
        QuizItem(
            quiz_type="mcq",
            question="다음 실행 대상을 결정하는 역할은?",
            options=[
                "Router",
                "Parser",
                "Formatter",
                "VectorStore",
            ],
            answer="Router",
            explanation=("Router는 상태를 기반으로 다음 실행 대상을 결정합니다."),
            source_chunk_ids=[
                "chunk-002",
            ],
        ),
    ]

    with pytest.raises(
        ValidationError,
        match="단답형",
    ):
        QuizLLMOutput(quiz_items=quiz_items)


def test_quiz_llm_output_accepts_optional_true_false() -> None:
    """객관식과 단답형에 true_false가 추가된 결과를 허용합니다."""

    quiz_items = _make_valid_quiz_items()

    quiz_items.append(
        QuizItem(
            quiz_type="true_false",
            question="StateGraph는 실행 흐름을 정의할 수 있다.",
            answer="True",
            explanation="StateGraph는 노드와 엣지를 사용해 실행 흐름을 정의합니다.",
            source_chunk_ids=["chunk-001"],
        )
    )

    result = QuizLLMOutput(quiz_items=quiz_items)

    assert {item.quiz_type for item in result.quiz_items} == {
        "mcq",
        "short",
        "true_false",
    }

    true_false_item = next(item for item in result.quiz_items if item.quiz_type == "true_false")

    assert true_false_item.options == [
        "True",
        "False",
    ]


def test_produce_quiz_items_returns_structured_quiz(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gemini Structured Output 결과가 QuizItem 목록으로 반환되는지 확인합니다."""

    state = _make_sample_state()

    expected_quiz_items = _make_valid_quiz_items()

    structured_model = MagicMock()

    structured_model.invoke.return_value = QuizLLMOutput(quiz_items=expected_quiz_items)

    model = MagicMock()

    model.with_structured_output.return_value = structured_model

    get_chat_model = MagicMock(return_value=model)

    monkeypatch.setattr(
        quiz_module,
        "get_chat_model",
        get_chat_model,
    )

    result = produce_quiz_items(state)

    get_chat_model.assert_called_once_with(role="generate")

    model.with_structured_output.assert_called_once_with(QuizLLMOutput)

    structured_model.invoke.assert_called_once()

    assert result == expected_quiz_items

    assert {item.quiz_type for item in result} == {
        "mcq",
        "short",
    }

    assert all(
        isinstance(
            item,
            QuizItem,
        )
        for item in result
    )


def test_produce_quiz_items_rejects_invalid_source_chunk_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """허용되지 않은 source_chunk_id가 포함된 퀴즈를 거부합니다."""

    state = _make_sample_state()

    invalid_quiz_items = [
        QuizItem(
            quiz_type="mcq",
            question="LangGraph의 그래프 객체는?",
            options=[
                "StateGraph",
                "ToolNode",
                "Document",
                "PromptTemplate",
            ],
            answer="StateGraph",
            explanation="StateGraph는 실행 그래프를 정의합니다.",
            source_chunk_ids=["chunk-999"],
        ),
        QuizItem(
            quiz_type="short",
            question="다음 실행 대상을 결정하는 역할은?",
            answer="Router",
            explanation="Router가 다음 실행 대상을 결정합니다.",
            source_chunk_ids=["chunk-002"],
        ),
    ]

    structured_model = MagicMock()
    structured_model.invoke.return_value = QuizLLMOutput(quiz_items=invalid_quiz_items)

    model = MagicMock()
    model.with_structured_output.return_value = structured_model

    get_chat_model = MagicMock(return_value=model)

    monkeypatch.setattr(
        quiz_module,
        "get_chat_model",
        get_chat_model,
    )

    with pytest.raises(
        ValueError,
        match="허용되지 않은",
    ):
        produce_quiz_items(state)
