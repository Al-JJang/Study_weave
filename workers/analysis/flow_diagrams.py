"""C — 파이프라인/커리큘럼/실행 흐름도. 연동: prompts.py, schemas.analysis.FlowDiagram, nodes.py"""

from __future__ import annotations

from pydantic import BaseModel

import config
from schemas.analysis import FlowDiagram
from schemas.files import RetrievedChunk
from workers.analysis.prompts import flow_diagram_prompt


class FlowDiagramList(BaseModel):
    """structured output 은 단일 모델만 받으므로 리스트를 감싸는 컨테이너."""

    flows: list[FlowDiagram]


def produce_flows(chunks: list[RetrievedChunk]) -> list[FlowDiagram]:
    if not chunks:
        return []

    # nodes.py 가 이 모듈을 import 하므로 순환 import 를 피하려고 호출 시점에 가져온다.
    from workers.analysis.nodes import build_evidence_context

    model = config.get_chat_model(role="generate").with_structured_output(FlowDiagramList)
    chain = flow_diagram_prompt() | model
    result: FlowDiagramList = chain.invoke({"evidence": build_evidence_context(chunks)})

    allowed_ids = {chunk.chunk_id for chunk in chunks}
    return [flow for flow in result.flows if set(flow.source_chunk_ids).issubset(allowed_ids)]
