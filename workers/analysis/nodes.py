"""
C — Graph Node (analyze).

route 별:
    pdf_only  → concepts (+ flows/tables 선택)
    code_only → code_units (+ flows/tables 선택)
    both      → 전부 + cross_references + practice_notes

반환 키(AnalysisOutput 필드와 동일): concepts, code_units, flows, tables, cross_references, practice_notes
※ AgentState 쪽 키 이름은 A 승인 후 확정 — 팀 공유 문서(docs/schema-migration-analysis.md) 참고.

연동: concept/code_flow/flow_diagrams/reference_tables/cross_reference/practice_notes, graph/supervisor.py, config.get_chat_model

WEAVE-22: concepts / code_units / cross_references 만 생성한다.
flows / tables / practice_notes 는 아직 티켓이 없어 빈 리스트로 반환한다.
"""

from __future__ import annotations

from schemas.files import RetrievedChunk
from schemas.state import AgentState
from workers.analysis.code_flow import produce_code_units
from workers.analysis.concept import produce_concepts
from workers.analysis.cross_reference import produce_cross_references


def build_evidence_context(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for chunk in chunks:
        if chunk.source_type == "pdf":
            location = f"page:{chunk.page_number}"
        else:
            location = f"line:{chunk.start_line}-{chunk.end_line}"
        blocks.append(f"[{chunk.chunk_id} | {location}]\n{chunk.content}")
    return "\n\n".join(blocks)


def analyze_node(state: AgentState) -> dict:
    route = state.get("route", "both")
    chunks = state.get("retrieved_chunks", [])

    concepts = produce_concepts(chunks) if route in ("pdf_only", "both") else []
    code_units = produce_code_units(chunks) if route in ("code_only", "both") else []
    cross_references = (
        produce_cross_references(chunks, concepts, code_units) if route == "both" else []
    )

    return {
        "status": "analyzed",
        "concepts": concepts,
        "code_units": code_units,
        "flows": [],
        "tables": [],
        "cross_references": cross_references,
        "practice_notes": [],
    }
