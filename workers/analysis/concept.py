"""C — PDF 개념 요약. 연동: prompts.py, schemas.analysis.ConceptItem, nodes.py"""

from __future__ import annotations

from pydantic import BaseModel

import config
from schemas.analysis import ConceptItem
from schemas.files import RetrievedChunk
from workers.analysis.prompts import concept_prompt


class ConceptList(BaseModel):
    """structured output 은 단일 모델만 받으므로 리스트를 감싸는 컨테이너."""

    concepts: list[ConceptItem]


def produce_concepts(chunks: list[RetrievedChunk]) -> list[ConceptItem]:
    pdf_chunks = [chunk for chunk in chunks if chunk.source_type == "pdf"]
    if not pdf_chunks:
        return []

    # nodes.py 가 이 모듈을 import 하므로 순환 import 를 피하려고 호출 시점에 가져온다.
    from workers.analysis.nodes import build_evidence_context

    model = config.get_chat_model(role="generate").with_structured_output(ConceptList)
    chain = concept_prompt() | model
    result: ConceptList = chain.invoke({"evidence": build_evidence_context(pdf_chunks)})

    allowed_ids = {chunk.chunk_id for chunk in pdf_chunks}
    return [
        concept
        for concept in result.concepts
        if set(concept.source_chunk_ids).issubset(allowed_ids)
    ]
