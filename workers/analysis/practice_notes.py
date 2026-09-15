"""C — 실수/주의/체크리스트 콜아웃. 연동: prompts.py, schemas.analysis.PracticeNote, nodes.py"""

from __future__ import annotations

from schemas.analysis import PracticeNote
from schemas.files import RetrievedChunk


def produce_practice_notes(chunks: list[RetrievedChunk]) -> list[PracticeNote]:
    raise NotImplementedError("C: produce_practice_notes")
