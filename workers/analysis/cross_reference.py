"""C — 이론 p.X ↔ 코드 줄 연결. 연동: prompts.py, schemas.analysis.CrossReferenceItem, nodes.py"""

from __future__ import annotations

from schemas.analysis import CrossReferenceItem
from schemas.files import RetrievedChunk


def produce_cross_references(chunks: list[RetrievedChunk]) -> list[CrossReferenceItem]:
    raise NotImplementedError("C: produce_cross_references")
