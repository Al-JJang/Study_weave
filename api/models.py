"""프론트엔드용 API 응답 모델. 팀 공유 schemas/ 계약은 건드리지 않는다."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SourceKind = Literal["pdf", "code", "text"]
MaterialKind = Literal["lecture", "code"]
RecordStatus = Literal["uploaded", "processing", "ready", "error", "draft"]
JobStatus = Literal["queued", "running", "done", "error"]
JobKind = Literal["upload", "note"]


class HealthResponse(BaseModel):
    status: str
    service: str
    graph_available: bool


class TeamUser(BaseModel):
    id: str
    name: str


class SourceItem(BaseModel):
    id: str
    filename: str
    source_type: SourceKind
    material_kind: MaterialKind = "lecture"
    size_bytes: int
    created_at: str
    status: RecordStatus
    user_id: str
    date_folder: str
    relative_path: str
    topic: str = "미분류"
    note_id: str | None = None


class NoteItem(BaseModel):
    id: str
    title: str
    preview: str
    markdown: str
    source_ids: list[str] = Field(default_factory=list)
    created_at: str
    status: RecordStatus
    user_id: str
    date_folder: str
    relative_path: str


class FolderUploadResponse(BaseModel):
    items: list[SourceItem]
    classified_by: Literal["gemini", "heuristic", "topic"]
    message: str


class NoteCreateRequest(BaseModel):
    title: str | None = None
    user_id: str | None = None


class JobItem(BaseModel):
    id: str
    kind: JobKind
    status: JobStatus
    message: str
    source_id: str | None = None
    note_id: str | None = None
    created_at: str
    user_id: str | None = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: list[ChatMessage] = Field(default_factory=list)


DeskItemKind = Literal["note", "source"]


class DeskItemRef(BaseModel):
    kind: DeskItemKind
    id: str


class DeskSectionRecord(BaseModel):
    id: str
    title: str
    items: list[DeskItemRef] = Field(default_factory=list)


class DeskRecord(BaseModel):
    user_id: str
    sections: list[DeskSectionRecord] = Field(default_factory=list)


class DeskItem(BaseModel):
    kind: DeskItemKind
    id: str
    title: str
    href: str
    preview: str | None = None


class DeskSection(BaseModel):
    id: str
    title: str
    items: list[DeskItem] = Field(default_factory=list)


class DeskResponse(BaseModel):
    user_id: str
    user_name: str
    sections: list[DeskSection] = Field(default_factory=list)
    unfiled: list[DeskItem] = Field(default_factory=list)


class DeskSectionCreate(BaseModel):
    user_id: str
    title: str


class DeskSectionRename(BaseModel):
    user_id: str
    title: str


class DeskMoveRequest(BaseModel):
    user_id: str
    kind: DeskItemKind
    item_id: str
    section_id: str | None = None
