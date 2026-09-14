"""C — 비교/요약 참조표. 연동: prompts.py, schemas.analysis.ReferenceTable, nodes.py"""

from __future__ import annotations

from schemas.analysis import ReferenceTable
from schemas.files import RetrievedChunk


def produce_tables(chunks: list[RetrievedChunk]) -> list[ReferenceTable]:
    raise NotImplementedError("C: produce_tables")
