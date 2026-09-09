"""
C — Graph Node (analyze).

route 별:
    pdf_only  → concept_summary
    code_only → code_analysis
    both      → 전부 + cross_references + troubleshooting

연동: concept/code_flow/cross_reference/troubleshooting, graph/supervisor.py, config.get_chat_model
"""

from __future__ import annotations

from schemas.files import RetrievedChunk
from schemas.state import AgentState


def build_evidence_context(chunks: list[RetrievedChunk]) -> str:
    raise NotImplementedError("C: build_evidence_context")


def analyze_node(state: AgentState) -> dict:
    raise NotImplementedError("C: analyze_node")
