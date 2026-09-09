"""C — PDF 개념 요약. 연동: prompts.py, schemas.analysis.ConceptItem, nodes.py"""

from __future__ import annotations

from schemas.analysis import ConceptItem
from schemas.files import RetrievedChunk


def produce_concept_summary(chunks: list[RetrievedChunk]) -> list[ConceptItem]:
    raise NotImplementedError("C: produce_concept_summary")
