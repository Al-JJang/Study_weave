"""C — 파이프라인/커리큘럼/실행 흐름도. 연동: prompts.py, schemas.analysis.FlowDiagram, nodes.py"""

from __future__ import annotations

from schemas.analysis import FlowDiagram
from schemas.files import RetrievedChunk


def produce_flows(chunks: list[RetrievedChunk]) -> list[FlowDiagram]:
    raise NotImplementedError("C: produce_flows")
