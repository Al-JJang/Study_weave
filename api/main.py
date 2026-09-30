"""StudyWeave AI FastAPI 앱.

제공 엔드포인트:
    GET  /api/health
    GET  /api/users
    GET  /api/sources?user_id=
    POST /api/sources          파일 업로드 (user_id 폼)
    GET  /api/notes?user_id=
    POST /api/notes            빈 노트 생성
    GET  /api/notes/{note_id}
    GET  /api/jobs?user_id=
    GET  /api/desk?user_id=
    POST /api/desk/sections
    PATCH /api/desk/sections/{section_id}
    DELETE /api/desk/sections/{section_id}
    POST /api/desk/move
    POST /api/chat             학습 도우미 (SSE)
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import api.desk as desk
import api.store as store
from api.chat import iter_chat_sse, prepare_chat
from api.models import (
    ChatRequest,
    DeskMoveRequest,
    DeskResponse,
    DeskSectionCreate,
    DeskSectionRename,
    HealthResponse,
    JobItem,
    NoteCreateRequest,
    NoteItem,
    SourceItem,
    SourceKind,
    TeamUser,
)
from api.paths import (
    normalize_topic,
    parse_study_date,
    sanitize_filename,
    today_folder,
    topic_slug,
    unique_path,
)
from api.pipeline import graph_available, try_mock_markdown
from api.users import list_team_users, require_user_id
from config import DATA_DIR

UPLOAD_DIR = DATA_DIR / "uploads"
NOTES_DIR = DATA_DIR / "notes"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024

CODE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp"}


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _source_type(filename: str) -> SourceKind:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in CODE_SUFFIXES:
        return "code"
    return "text"


def _preview(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            return stripped[:160]
    return fallback[:160]


def _title_from_markdown(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()[:80]
    return fallback


def _write_note_file(user_id: str, date_folder: str, title: str, markdown: str) -> tuple[str, str]:
    safe_name = sanitize_filename(f"{title}.md")
    dest = unique_path(NOTES_DIR / user_id / date_folder, safe_name)
    dest.write_text(markdown, encoding="utf-8")
    return dest.name, f"{user_id}/{date_folder}/{dest.name}"


def create_app(*, seed: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        desk.DESK_DIR.mkdir(parents=True, exist_ok=True)
        store.reset(seed=seed)
        yield

    application = FastAPI(title="StudyWeave AI", version="0.1.0", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service="studyweave-ai",
            graph_available=graph_available(),
        )

    @application.get("/api/users", response_model=list[TeamUser])
    def users() -> list[TeamUser]:
        return [TeamUser(**row) for row in list_team_users()]

    @application.get("/api/sources", response_model=list[SourceItem])
    def list_sources(user_id: str | None = None) -> list[SourceItem]:
        return store.list_sources(user_id=require_user_id(user_id))

    @application.post("/api/sources", response_model=SourceItem, status_code=201)
    async def upload_source(
        file: Annotated[UploadFile, File()],
        user_id: Annotated[str | None, Form()] = None,
        topic: Annotated[str | None, Form()] = None,
        study_date: Annotated[str | None, Form()] = None,
    ) -> SourceItem:
        uid = require_user_id(user_id)
        filename = (file.filename or "").strip()
        if not filename:
            raise HTTPException(status_code=400, detail="파일 이름이 필요합니다.")

        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="빈 파일은 업로드할 수 없습니다.")
        if len(payload) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="파일 크기는 20MB 이하여야 합니다.")

        source_id = f"src-{uuid.uuid4().hex[:10]}"
        try:
            date_folder = parse_study_date(study_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        topic_name = normalize_topic(topic)
        slug = topic_slug(topic_name)
        safe_name = sanitize_filename(filename)
        dest = unique_path(UPLOAD_DIR / uid / date_folder / slug, safe_name)
        dest.write_bytes(payload)
        relative_path = f"{uid}/{date_folder}/{slug}/{dest.name}"

        created = _now()
        source = SourceItem(
            id=source_id,
            filename=dest.name,
            source_type=_source_type(dest.name),
            size_bytes=len(payload),
            created_at=created,
            status="processing",
            user_id=uid,
            date_folder=date_folder,
            relative_path=relative_path,
            topic=topic_name,
        )
        store.upsert_source(source)

        job = JobItem(
            id=f"job-{uuid.uuid4().hex[:10]}",
            kind="upload",
            status="running",
            message="파일을 저장했습니다. 학습 노트를 준비합니다.",
            source_id=source_id,
            created_at=created,
            user_id=uid,
        )
        store.upsert_job(job)

        markdown = try_mock_markdown()
        if markdown:
            title = _title_from_markdown(markdown, Path(dest.name).stem)
            _, note_rel = _write_note_file(uid, date_folder, title, markdown)
            note = NoteItem(
                id=f"note-{uuid.uuid4().hex[:10]}",
                title=title,
                preview=_preview(markdown, title),
                markdown=markdown,
                source_ids=[source_id],
                created_at=_now(),
                status="ready",
                user_id=uid,
                date_folder=date_folder,
                relative_path=note_rel,
            )
            source = source.model_copy(update={"status": "ready", "note_id": note.id})
            job = job.model_copy(
                update={
                    "status": "done",
                    "note_id": note.id,
                    "message": "mock 파이프라인으로 노트를 만들었습니다.",
                }
            )
            store.upsert_note(note)
        else:
            title = Path(dest.name).stem
            markdown = (
                f"# {title}\n\n"
                "업로드는 완료됐습니다. 분석 그래프가 연결되면 이 자리에 "
                "개념·코드·퀴즈 노트가 채워집니다.\n"
            )
            _, note_rel = _write_note_file(uid, date_folder, title, markdown)
            note = NoteItem(
                id=f"note-{uuid.uuid4().hex[:10]}",
                title=title,
                preview="그래프가 아직 없어 placeholder 노트를 만들었습니다.",
                markdown=markdown,
                source_ids=[source_id],
                created_at=_now(),
                status="draft",
                user_id=uid,
                date_folder=date_folder,
                relative_path=note_rel,
            )
            source = source.model_copy(update={"status": "ready", "note_id": note.id})
            job = job.model_copy(
                update={
                    "status": "done",
                    "note_id": note.id,
                    "message": "그래프가 없어 placeholder 노트를 만들었습니다.",
                }
            )
            store.upsert_note(note)

        store.upsert_source(source)
        store.upsert_job(job)
        return source

    @application.get("/api/notes", response_model=list[NoteItem])
    def list_notes(user_id: str | None = None) -> list[NoteItem]:
        return store.list_notes(user_id=require_user_id(user_id))

    @application.post("/api/notes", response_model=NoteItem, status_code=201)
    def create_note(body: NoteCreateRequest | None = None) -> NoteItem:
        uid = require_user_id(body.user_id if body else None)
        title = (body.title if body and body.title else "새 노트").strip() or "새 노트"
        date_folder = today_folder()
        markdown = (
            f"# {title}\n\n"
            "빈 노트입니다. 대시보드에서 소스를 업로드하면 분석 결과가 이 형식으로 쌓입니다.\n"
        )
        _, note_rel = _write_note_file(uid, date_folder, title, markdown)
        note = NoteItem(
            id=f"note-{uuid.uuid4().hex[:10]}",
            title=title,
            preview="아직 본문이 없습니다. 소스를 올리면 학습 노트가 채워집니다.",
            markdown=markdown,
            source_ids=[],
            created_at=_now(),
            status="draft",
            user_id=uid,
            date_folder=date_folder,
            relative_path=note_rel,
        )
        store.upsert_note(note)
        store.upsert_job(
            JobItem(
                id=f"job-{uuid.uuid4().hex[:10]}",
                kind="note",
                status="done",
                message="빈 노트를 만들었습니다.",
                note_id=note.id,
                created_at=note.created_at,
                user_id=uid,
            )
        )
        return note

    @application.get("/api/notes/{note_id}", response_model=NoteItem)
    def get_note(note_id: str) -> NoteItem:
        note = store.get_note(note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="노트를 찾을 수 없습니다.")
        return note

    @application.get("/api/jobs", response_model=list[JobItem])
    def list_jobs(user_id: str | None = None) -> list[JobItem]:
        return store.list_jobs(user_id=require_user_id(user_id))

    @application.get("/api/desk", response_model=DeskResponse)
    def get_desk(user_id: str | None = None) -> DeskResponse:
        return desk.build_response(require_user_id(user_id))

    @application.post("/api/desk/sections", response_model=DeskResponse, status_code=201)
    def create_desk_section(body: DeskSectionCreate) -> DeskResponse:
        return desk.create_section(body)

    @application.patch("/api/desk/sections/{section_id}", response_model=DeskResponse)
    def rename_desk_section(section_id: str, body: DeskSectionRename) -> DeskResponse:
        return desk.rename_section(section_id, body)

    @application.delete("/api/desk/sections/{section_id}", response_model=DeskResponse)
    def delete_desk_section(section_id: str, user_id: str | None = None) -> DeskResponse:
        return desk.delete_section(section_id, user_id)

    @application.post("/api/desk/move", response_model=DeskResponse)
    def move_desk_item(body: DeskMoveRequest) -> DeskResponse:
        return desk.move_item(body)

    @application.post("/api/chat")
    def chat(body: ChatRequest) -> StreamingResponse:
        model, uid = prepare_chat(body)
        return StreamingResponse(
            iter_chat_sse(model, body, uid),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return application


app = create_app(seed=True)
