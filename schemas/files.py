"""
B 계약 — 파일 / Chunk / 출처.

연동:
    씀 ← workers/parser/*, store/vector_store.py, mocks/data.py
    읽힘 → workers/analysis/*, workers/formatter/*, graph/verify.py

chunk_id = {document_id}:chunk:{index:04d}
document_id = {request_id}:{safe_filename}
PDF → page_number 1-based / 코드 → start_line, end_line 1-based
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SourceType = Literal["pdf", "code"]


class FileInfo(BaseModel):
    document_id: str = Field(description="B가 생성. {request_id}:{safe_filename}")
    filename: str
    source_type: SourceType
    path: str
    title: str | None = None
    size_bytes: int | None = None
    code_line_count: int | None = None


class Chunk(BaseModel):
    chunk_id: str = Field(description="B가 생성. {document_id}:chunk:{index:04d}")
    document_id: str
    source_type: SourceType
    content: str
    chunk_index: int = Field(ge=0)
    page_number: int | None = Field(default=None, ge=1)
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)


class RetrievedChunk(Chunk):
    distance: float | None = None
    vector_rank: int | None = None
    retrieval_sources: list[str] = Field(default_factory=lambda: ["vector"])
