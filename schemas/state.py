"""
A 계약 — LangGraph AgentState.

규칙:
    Node 는 자신이 만든 key 만 반환한다.
    리스트 빈 결과 = []  (key 생략 금지, None 금지)
    문자열 미생성 = None
"""

from __future__ import annotations

from typing import Literal, Optional, TypedDict

from schemas.analysis import (
    CodeAnalysisItem,
    ConceptItem,
    CrossReferenceItem,
    TroubleshootingItem,
)
from schemas.errors import NodeError, VerificationReport
from schemas.files import Chunk, FileInfo, RetrievedChunk
from schemas.quiz import QuizItem

RouteType = Literal["pdf_only", "code_only", "both"]
StatusType = Literal[
    "received",
    "parsed",
    "retrieved",
    "analyzed",
    "formatted",
    "verified",
    "completed",
    "failed",
]


class AgentState(TypedDict, total=False):
    request_id: str
    files: list[FileInfo]
    parsed_chunks: list[Chunk]
    retrieved_chunks: list[RetrievedChunk]
    concept_summary: list[ConceptItem]
    code_analysis: list[CodeAnalysisItem]
    cross_references: list[CrossReferenceItem]
    troubleshooting: list[TroubleshootingItem]
    quiz_items: list[QuizItem]
    final_markdown: Optional[str]
    route: RouteType
    status: StatusType
    errors: list[NodeError]
    retry_count: int
    verification: Optional[VerificationReport]
