"""
D 계약 — 객관식 + 단답형 필수, True/False 선택 허용 복습 퀴즈.

연동:
    씀 ← workers/formatter/quiz.py
    읽힘 → workers/formatter/markdown.py, graph/verify.py, ui/tabs.py
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

QuizType = Literal[
    "mcq",
    "short",
    "true_false",
]


class QuizItem(BaseModel):
    """복습 퀴즈 한 문항의 데이터 구조입니다.

    Attributes:
        quiz_type: 퀴즈 유형. 객관식, 단답형 또는 True/False.
        question: 문제 내용.
        options: 객관식은 보기 목록, 단답형은 빈 리스트, True/False는 ["True", "False"]를 사용.
        answer: 정답 문자열. 객관식은 보기 문자열, 단답형은 단답 정답 문자열, True/False는 True 또는 False.
        explanation: 정답에 대한 해설.
        source_chunk_ids: 문제 생성에 사용된 근거 Chunk ID 목록.
    """

    quiz_type: QuizType

    question: str

    options: list[str] = Field(
        default_factory=list,
        description=(
            "mcq는 보기 목록을 사용하고, "
            "short는 빈 리스트, "
            "true_false는 ['True', 'False']를 사용합니다."
        ),
    )

    answer: str = Field(
        description=(
            "mcq는 보기 문자열 그대로 사용하고, "
            "short는 단답 정답 문자열을 사용하며, "
            "true_false는 True 또는 False를 사용합니다."
        )
    )

    explanation: str

    source_chunk_ids: list[str] = Field(min_length=1)

    @field_validator(
        "question",
        "answer",
        "explanation",
    )
    @classmethod
    def validate_non_empty_text(
        cls,
        value: str,
    ) -> str:
        """문제, 정답, 해설이 빈 문자열인지 검사합니다.

        Args:
            value: 검증할 문자열.

        Returns:
            검증을 통과한 문자열.

        Raises:
            ValueError: 문자열이 비어 있거나 공백만 있는 경우.
        """

        if not value.strip():
            raise ValueError("문제, 정답, 해설은 비어 있을 수 없습니다.")

        return value

    @model_validator(mode="after")
    def validate_quiz_by_type(self) -> QuizItem:
        """퀴즈 유형별 보기와 정답 규칙을 검사하고 정규화합니다.

        Returns:
            유형별 검증 및 정규화를 통과한 QuizItem.

        Raises:
            ValueError: 객관식 보기가 없거나 정답이 보기에 없는 경우,
                또는 True/False 정답이 True나 False가 아닌 경우.
        """

        if self.quiz_type == "mcq":
            if not self.options:
                raise ValueError("객관식 문제는 보기가 필요합니다.")

            self.options = [option.strip() for option in self.options]

            normalized_answer = self.answer.strip()

            if normalized_answer not in self.options:
                raise ValueError("객관식 정답은 보기 중 하나와 정확히 일치해야 합니다.")

            self.answer = normalized_answer

        elif self.quiz_type == "true_false":
            normalized_answer = self.answer.strip().lower()

            if normalized_answer not in [
                "true",
                "false",
            ]:
                raise ValueError("true_false 문제의 정답은 True 또는 False여야 합니다.")

            self.answer = normalized_answer.capitalize()

            self.options = [
                "True",
                "False",
            ]

        return self
