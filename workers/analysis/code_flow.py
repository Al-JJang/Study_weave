"""C — 코드 실행 순서·데이터 흐름·문법. 연동: prompts.py, schemas.analysis.CodeAnalysisItem, nodes.py"""

from __future__ import annotations

from schemas.analysis import CodeAnalysisItem
from schemas.files import RetrievedChunk


def produce_code_units(chunks: list[RetrievedChunk]) -> list[CodeAnalysisItem]:
    raise NotImplementedError("C: produce_code_units")
