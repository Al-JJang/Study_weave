"""C — 비교/요약 참조표. 연동: prompts.py, schemas.analysis.ReferenceTable, nodes.py"""

from __future__ import annotations

from pydantic import BaseModel

import config
from schemas.analysis import ReferenceTable
from schemas.files import RetrievedChunk
from workers.analysis.prompts import reference_table_prompt


class ReferenceTableList(BaseModel):
    """structured output 은 단일 모델만 받으므로 리스트를 감싸는 컨테이너."""

    tables: list[ReferenceTable]


def produce_tables(chunks: list[RetrievedChunk]) -> list[ReferenceTable]:
    if not chunks:
        return []

    # nodes.py 가 이 모듈을 import 하므로 순환 import 를 피하려고 호출 시점에 가져온다.
    from workers.analysis.nodes import build_evidence_context

    model = config.get_chat_model(role="generate").with_structured_output(ReferenceTableList)
    chain = reference_table_prompt() | model
    result: ReferenceTableList = chain.invoke({"evidence": build_evidence_context(chunks)})

    allowed_ids = {chunk.chunk_id for chunk in chunks}
    return [
        table
        for table in result.tables
        if set(table.source_chunk_ids).issubset(allowed_ids) and _rows_match_columns(table)
    ]


def _rows_match_columns(table: ReferenceTable) -> bool:
    """행 길이가 열 개수와 다르면 포맷터에서 Markdown 표가 깨진다."""
    return all(len(row) == len(table.columns) for row in table.rows)
