"""C — 실수/주의 콜아웃. 연동: prompts.py, schemas.analysis.TroubleshootingItem, nodes.py"""

from __future__ import annotations

from schemas.analysis import TroubleshootingItem
from schemas.files import RetrievedChunk


def produce_troubleshooting(chunks: list[RetrievedChunk]) -> list[TroubleshootingItem]:
    raise NotImplementedError("C: produce_troubleshooting")
