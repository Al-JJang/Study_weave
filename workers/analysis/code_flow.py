"""C — 코드 실행 순서·데이터 흐름·문법. 연동: prompts.py, schemas.analysis.CodeAnalysisItem, nodes.py"""

from __future__ import annotations

from pydantic import BaseModel

import config
from schemas.analysis import CodeAnalysisItem
from schemas.files import RetrievedChunk
from workers.analysis.prompts import code_flow_prompt


class CodeUnitList(BaseModel):
    """structured output 은 단일 모델만 받으므로 리스트를 감싸는 컨테이너."""

    code_units: list[CodeAnalysisItem]


def produce_code_units(chunks: list[RetrievedChunk]) -> list[CodeAnalysisItem]:
    code_chunks = [chunk for chunk in chunks if chunk.source_type == "code"]
    if not code_chunks:
        return []

    # nodes.py 가 이 모듈을 import 하므로 순환 import 를 피하려고 호출 시점에 가져온다.
    from workers.analysis.nodes import build_evidence_context

    model = config.get_chat_model(role="generate").with_structured_output(CodeUnitList)
    chain = code_flow_prompt() | model
    result: CodeUnitList = chain.invoke({"evidence": build_evidence_context(code_chunks)})

    allowed_ids = {chunk.chunk_id for chunk in code_chunks}
    return [unit for unit in result.code_units if set(unit.source_chunk_ids).issubset(allowed_ids)]
