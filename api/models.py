"""프론트엔드용 API 응답 모델. 팀 공유 schemas/ 계약은 건드리지 않는다."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SourceKind = Literal["pdf", "code", "text"]
RecordStatus = Literal["uploaded", "processing", "ready", "error", "draft"]
JobStatus = Literal["queued", "running", "done", "error"]
JobKind = Literal["upload", "note"]


class HealthResponse(BaseModel):
    status: str
    service: str
    graph_available: bool


class SourceItem(BaseModel):
    id: str
    filename: str
    source_type: SourceKind
    size_bytes: int
    created_at: str
    status: RecordStatus
    note_id: str | None = None


class NoteItem(BaseModel):
    id: str
    title: str
    preview: str
    markdown: str
    source_ids: list[str] = Field(default_factory=list)
    created_at: str
    status: RecordStatus


class NoteCreateRequest(BaseModel):
    title: str | None = None


class JobItem(BaseModel):
    id: str
    kind: JobKind
    status: JobStatus
    message: str
    source_id: str | None = None
    note_id: str | None = None
    created_at: str
