"""
C — Graph Node (analyze).

route 별:
    pdf_only  → concepts (+ flows/tables 선택)
    code_only → code_units (+ flows/tables 선택)
    both      → 전부 + cross_references + practice_notes

반환 키(AnalysisOutput 필드와 동일): concepts, code_units, flows, tables, cross_references, practice_notes
※ AgentState 쪽 키 이름은 A 승인 후 확정 — 팀 공유 문서(docs/schema-migration-analysis.md) 참고.

연동: concept/code_flow/flow_diagrams/reference_tables/cross_reference/practice_notes, graph/supervisor.py, config.get_chat_model
"""

from __future__ import annotations

from schemas.files import RetrievedChunk
from schemas.state import AgentState


def build_evidence_context(chunks: list[RetrievedChunk]) -> str:
    raise NotImplementedError("C: build_evidence_context")


def analyze_node(state: AgentState) -> dict:
    raise NotImplementedError("C: analyze_node")
