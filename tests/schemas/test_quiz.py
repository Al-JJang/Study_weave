"""
QuizItem 검증 테스트.

확인 항목:
1. 문제, 정답, 해설이 빈 문자열 또는 공백만 있으면 거부
2. 객관식 문제에 보기가 없으면 거부
3. 객관식 정답이 보기 안에 없으면 거부
4. 객관식 정답이 보기 안에 있으면 허용
5. 객관식 보기와 정답의 앞뒤 공백을 정규화
6. 단답형 문제는 보기를 작성하지 않아도 허용
7. mcq, short, true_false 이외의 퀴즈 유형은 거부
8. source_chunk_ids가 비어 있으면 거부
9. true_false 문제는 True 또는 False 정답을 허용
10. true_false 문제의 공백과 대소문자를 정규화
11. true_false 문제에서 True 또는 False 이외의 정답은 거부
"""

import pytest
from pydantic import ValidationError

from schemas.quiz import QuizItem


@pytest.mark.parametrize(
    "field",
    [
        "question",
        "answer",
        "explanation",
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
    ],
)
def test_quiz_rejects_empty_text(
    field: str,
    value: str,
) -> None:
    """문제, 정답, 해설에 빈 문자열이나 공백만 들어가면 거부합니다."""

    data = {
        "quiz_type": "short",
        "question": "실행 순서를 정의하는 객체는?",
        "answer": "StateGraph",
        "explanation": "StateGraph는 노드와 엣지로 실행 순서를 정의합니다.",
        "source_chunk_ids": ["chunk-001"],
    }

    data[field] = value

    with pytest.raises(ValidationError) as exc_info:
        QuizItem(**data)

    assert any(
        error["loc"] == (field,) and error["type"] == "value_error"
        for error in exc_info.value.errors()
    )


def test_mcq_rejects_empty_options() -> None:
    """객관식 문제에 보기가 없으면 거부합니다."""

    with pytest.raises(
        ValidationError,
        match="객관식 문제는 보기가 필요합니다",
    ):
        QuizItem(
            quiz_type="mcq",
            question="실행 순서를 정의하는 객체는?",
            options=[],
            answer="StateGraph",
            explanation="StateGraph는 노드와 엣지로 실행 순서를 정의합니다.",
            source_chunk_ids=["chunk-001"],
        )


def test_mcq_rejects_answer_outside_options() -> None:
    """객관식 정답이 보기 목록에 포함되지 않으면 거부합니다."""

    with pytest.raises(
        ValidationError,
        match="객관식 정답은",
    ):
        QuizItem(
            quiz_type="mcq",
            question="실행 순서를 정의하는 객체는?",
            options=[
                "MessagesState",
                "ToolNode",
                "PersistentClient",
                "Document",
            ],
            answer="StateGraph",
            explanation="StateGraph는 노드와 엣지로 실행 순서를 정의합니다.",
            source_chunk_ids=["chunk-001"],
        )


def test_mcq_accepts_answer_in_options() -> None:
    """객관식 정답이 보기 목록에 포함되어 있으면 허용합니다."""

    quiz = QuizItem(
        quiz_type="mcq",
        question="실행 순서를 정의하는 객체는?",
        options=[
            "StateGraph",
            "MessagesState",
            "ToolNode",
            "Document",
        ],
        answer="StateGraph",
        explanation="StateGraph는 노드와 엣지로 실행 순서를 정의합니다.",
        source_chunk_ids=["chunk-001"],
    )

    assert quiz.quiz_type == "mcq"
    assert quiz.answer == "StateGraph"
    assert quiz.answer in quiz.options


def test_mcq_normalizes_whitespace() -> None:
    """객관식 보기와 정답의 앞뒤 공백을 제거합니다."""

    quiz = QuizItem(
        quiz_type="mcq",
        question="실행 순서를 정의하는 객체는?",
        options=[
            " StateGraph ",
            " ToolNode ",
            " Document ",
            " PromptTemplate ",
        ],
        answer=" StateGraph ",
        explanation="StateGraph는 노드와 엣지로 실행 순서를 정의합니다.",
        source_chunk_ids=["chunk-001"],
    )

    assert quiz.options == [
        "StateGraph",
        "ToolNode",
        "Document",
        "PromptTemplate",
    ]

    assert quiz.answer == "StateGraph"


def test_short_quiz_allows_missing_options() -> None:
    """단답형 문제는 options를 작성하지 않아도 허용합니다."""

    quiz = QuizItem(
        quiz_type="short",
        question="실행 순서를 정의하는 객체는?",
        answer="StateGraph",
        explanation="StateGraph는 노드와 엣지로 실행 순서를 정의합니다.",
        source_chunk_ids=["chunk-001"],
    )

    assert quiz.quiz_type == "short"
    assert quiz.options == []
    assert quiz.answer == "StateGraph"


def test_quiz_rejects_unsupported_type() -> None:
    """mcq, short, true_false 이외의 퀴즈 유형은 거부합니다."""

    with pytest.raises(ValidationError):
        QuizItem(
            quiz_type="essay",
            question="StateGraph는 실행 흐름을 정의한다.",
            answer="True",
            explanation="StateGraph는 노드와 엣지로 실행 흐름을 정의합니다.",
            source_chunk_ids=["chunk-001"],
        )


def test_quiz_rejects_empty_source_chunk_ids() -> None:
    """출처 Chunk ID가 하나도 없으면 거부합니다."""

    with pytest.raises(ValidationError):
        QuizItem(
            quiz_type="short",
            question="실행 순서를 정의하는 객체는?",
            answer="StateGraph",
            explanation="StateGraph는 노드와 엣지로 실행 순서를 정의합니다.",
            source_chunk_ids=[],
        )


@pytest.mark.parametrize(
    "answer",
    [
        "True",
        "False",
    ],
)
def test_true_false_accepts_valid_answer(
    answer: str,
) -> None:
    """True/False 문제의 정상 정답을 허용합니다."""

    quiz = QuizItem(
        quiz_type="true_false",
        question="StateGraph는 실행 흐름을 정의할 수 있다.",
        answer=answer,
        explanation="StateGraph는 노드와 엣지를 사용해 실행 흐름을 정의합니다.",
        source_chunk_ids=["chunk-001"],
    )

    assert quiz.quiz_type == "true_false"
    assert quiz.options == [
        "True",
        "False",
    ]
    assert quiz.answer == answer


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("true", "True"),
        ("TRUE", "True"),
        (" True ", "True"),
        ("false", "False"),
        ("FALSE", "False"),
        (" False ", "False"),
    ],
)
def test_true_false_normalizes_answer(
    answer: str,
    expected: str,
) -> None:
    """True/False 정답의 공백과 대소문자를 정규화합니다."""

    quiz = QuizItem(
        quiz_type="true_false",
        question="StateGraph는 실행 흐름을 정의할 수 있다.",
        answer=answer,
        explanation="StateGraph는 노드와 엣지를 사용해 실행 흐름을 정의합니다.",
        source_chunk_ids=["chunk-001"],
    )

    assert quiz.options == [
        "True",
        "False",
    ]

    assert quiz.answer == expected


def test_true_false_rejects_invalid_answer() -> None:
    """True/False 문제에서 True 또는 False 이외의 정답은 거부합니다."""

    with pytest.raises(
        ValidationError,
        match="True 또는 False",
    ):
        QuizItem(
            quiz_type="true_false",
            question="StateGraph는 실행 흐름을 정의할 수 있다.",
            answer="Yes",
            explanation="StateGraph는 노드와 엣지를 사용해 실행 흐름을 정의합니다.",
            source_chunk_ids=["chunk-001"],
        )
