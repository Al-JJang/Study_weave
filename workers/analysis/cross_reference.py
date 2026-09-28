"""C — 개념↔코드 매칭/단독 항목 분류(ref_type: matched/code_only/concept_only). 연동: prompts.py, schemas.analysis.CrossReferenceItem, nodes.py"""

from __future__ import annotations

from pydantic import BaseModel

import config
from schemas.analysis import CodeAnalysisItem, ConceptItem, CrossReferenceItem
from schemas.files import RetrievedChunk
from workers.analysis.prompts import cross_reference_prompt


class CrossReferenceList(BaseModel):
    """structured output 은 단일 모델만 받으므로 리스트를 감싸는 컨테이너."""

    cross_references: list[CrossReferenceItem]


def produce_cross_references(
    chunks: list[RetrievedChunk],
    concepts: list[ConceptItem],
    code_units: list[CodeAnalysisItem],
) -> list[CrossReferenceItem]:
    if not concepts and not code_units:
        return []

    # nodes.py 가 이 모듈을 import 하므로 순환 import 를 피하려고 호출 시점에 가져온다.
    from workers.analysis.nodes import build_evidence_context

    model = config.get_chat_model(role="generate").with_structured_output(CrossReferenceList)
    chain = cross_reference_prompt() | model
    result: CrossReferenceList = chain.invoke(
        {
            "concepts": _format_concepts(concepts),
            "code_units": _format_code_units(code_units),
            "evidence": build_evidence_context(chunks),
        }
    )

    allowed_ids = {chunk.chunk_id for chunk in chunks}
    return [
        item for item in result.cross_references if set(item.source_chunk_ids).issubset(allowed_ids)
    ]


def _format_concepts(concepts: list[ConceptItem]) -> str:
    return "\n".join(f"- {concept.concept_id}: {concept.title}" for concept in concepts)


def _format_code_units(code_units: list[CodeAnalysisItem]) -> str:
    return "\n".join(f"- {unit.unit_name} ({unit.unit_type})" for unit in code_units)
