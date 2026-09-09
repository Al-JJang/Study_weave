"""
A 계약 — Node 에러 / 검증 리포트.

연동:
    씀 ← graph/verify.py, graph/supervisor.py
    읽힘 → ui/app.py (실패 표시)
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class NodeError(BaseModel):
    node: str
    error_code: str
    message: str
    retryable: bool = False


class VerificationReport(BaseModel):
    """팀장(A) 검증 에이전트. 규칙 검증이 1순위, LLM 은 선택."""

    passed: bool
    issues: list[str] = Field(default_factory=list)
    dropped_quiz_ids: list[int] = Field(default_factory=list)
