"""C — 실수/주의/체크리스트 콜아웃. 연동: prompts.py, schemas.analysis.PracticeNote, nodes.py"""

from __future__ import annotations

from pydantic import BaseModel

import config
from schemas.analysis import PracticeNote
from schemas.files import RetrievedChunk
from workers.analysis.prompts import practice_note_prompt


class PracticeNoteList(BaseModel):
    """structured output 은 단일 모델만 받으므로 리스트를 감싸는 컨테이너."""

    practice_notes: list[PracticeNote]


def produce_practice_notes(chunks: list[RetrievedChunk]) -> list[PracticeNote]:
    if not chunks:
        return []

    # nodes.py 가 이 모듈을 import 하므로 순환 import 를 피하려고 호출 시점에 가져온다.
    from workers.analysis.nodes import build_evidence_context

    model = config.get_chat_model(role="generate").with_structured_output(PracticeNoteList)
    chain = practice_note_prompt() | model
    result: PracticeNoteList = chain.invoke({"evidence": build_evidence_context(chunks)})

    allowed_ids = {chunk.chunk_id for chunk in chunks}
    return [
        note for note in result.practice_notes if set(note.source_chunk_ids).issubset(allowed_ids)
    ]
