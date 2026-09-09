"""
D 계약 — 복습 퀴즈 3~5문항.

연동:
    씀 ← workers/formatter/quiz.py
    읽힘 → workers/formatter/markdown.py, graph/verify.py, ui/tabs.py
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

QuizType = Literal["mcq", "short", "true_false"]


class QuizItem(BaseModel):
    quiz_type: QuizType
    question: str
    options: list[str] = Field(
        default_factory=list,
        description="mcq 는 4개 권장. short/true_false 는 빈 리스트 가능",
    )
    answer: str = Field(description="보기 문자열 그대로. 번호/인덱스가 아님")
    explanation: str
    source_chunk_ids: list[str] = Field(min_length=1)
