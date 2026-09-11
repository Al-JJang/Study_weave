"""
A 계약 — Node 에러 / 검증 리포트.

연동:
    씀 ← graph/verify.py, graph/supervisor.py
    읽힘 → ui/app.py (실패 표시)
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ErrorCode = Literal[
    "PARSE_FAIL",  # PDF/코드 파싱 실패
    "EMPTY_SECTION",  # 마크다운 섹션이 비었음
    "CITATION_MISSING",  # source_chunk_ids 누락
    "HALLUCINATED_CHUNK_ID",  # 존재하지 않는 chunk_id 인용
    "LLM_TIMEOUT",  # llm api 요청 타임아웃
    "LLM_PARSE_FAIL",  # structured output 파싱/검증 실패
    "QUIZ_ANSWER_MISMATCH",  # answer가 options에 없음
]


class NodeError(BaseModel):
    node: str
    error_code: ErrorCode
    message: str
    retryable: bool = False


class VerificationReport(BaseModel):
    """팀장(A) 검증 에이전트. 규칙 검증이 1순위, LLM 은 선택."""

    passed: bool
    issues: list[str] = Field(default_factory=list)
    dropped_quiz_ids: list[int] = Field(default_factory=list)
