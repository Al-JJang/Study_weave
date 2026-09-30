"""StudyWeave AI FastAPI 앱.

제공 엔드포인트:
    GET  /api/health
    GET  /api/users
    GET  /api/sources?kind=lecture|code
    POST /api/sources          강사 자료 업로드 (user_id, material_kind 폼)
    POST /api/sources/folder   코드 폴더 업로드 후 주제 분류
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
from api.classify import (
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_FOLDER_BYTES,
    FolderEntry,
    classify_folder,
    heuristic_topic,
    snippet_from_bytes,
)
from api.models import (
    ChatRequest,
    DeskMoveRequest,
    DeskResponse,
    DeskSectionCreate,
    DeskSectionRename,
    FolderUploadResponse,
    HealthResponse,
    JobItem,
    MaterialKind,
    NoteCreateRequest,
    NoteItem,
    SourceItem,
    SourceKind,
    TeamUser,
)
from api.paths import (
    CODE_SUFFIXES,
    is_code_folder_file,
    normalize_relpath,
    normalize_topic,
    parse_material_kind,
    parse_study_date,
    sanitize_filename,
    sanitize_relpath,
    should_skip_relpath,
    strip_root_segment,
    today_folder,
    topic_slug,
    unique_path,
)
from api.pipeline import graph_available
from api.users import list_team_users, require_user_id
from config import DATA_DIR

UPLOAD_DIR = DATA_DIR / "uploads"
NOTES_DIR = DATA_DIR / "notes"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _source_type(filename: str) -> SourceKind:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in CODE_SUFFIXES:
        return "code"
    return "text"


def _form_list(value: list[str] | str | None, size: int) -> list[str]:
    if value is None:
        items: list[str] = []
    elif isinstance(value, str):
        items = [value]
    else:
        items = list(value)
    if len(items) < size:
        items.extend([""] * (size - len(items)))
    return items[:size]


def _persist_source(
    *,
    uid: str,
    payload: bytes,
    date_folder: str,
    topic_name: str,
    material_kind: MaterialKind,
    inner_path: str,
) -> SourceItem:
    slug = topic_slug(topic_name)
    rel = sanitize_relpath(inner_path)
    name = Path(rel).name
    parent = Path(rel).parent
    directory = UPLOAD_DIR / material_kind / date_folder / slug
    if parent.parts and parent.as_posix() != ".":
        directory = directory / parent
    dest = unique_path(directory, name)
    dest.write_bytes(payload)
    topic_root = UPLOAD_DIR / material_kind / date_folder / slug
    inner = dest.relative_to(topic_root).as_posix()
    created = _now()
    source = SourceItem(
        id=f"src-{uuid.uuid4().hex[:10]}",
        filename=inner,
        source_type=_source_type(dest.name),
        material_kind=material_kind,
        size_bytes=len(payload),
        created_at=created,
        status="ready",
        user_id=uid,
        date_folder=date_folder,
        relative_path=f"{material_kind}/{date_folder}/{slug}/{inner}",
        topic=topic_name,
    )
    store.upsert_source(source)
    return source


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
    def list_sources(kind: str | None = None) -> list[SourceItem]:
        material = None
        if kind is not None and kind.strip():
            text = kind.strip().lower()
            if text not in {"lecture", "code"}:
                raise HTTPException(status_code=400, detail="kind는 lecture 또는 code 여야 합니다.")
            material = text
        return store.list_sources(material_kind=material)

    @application.post("/api/sources", response_model=SourceItem, status_code=201)
    async def upload_source(
        file: Annotated[UploadFile, File()],
        user_id: Annotated[str | None, Form()] = None,
        topic: Annotated[str | None, Form()] = None,
        study_date: Annotated[str | None, Form()] = None,
        material_kind: Annotated[str | None, Form()] = None,
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

        try:
            date_folder = parse_study_date(study_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        topic_name = normalize_topic(topic)
        kind = parse_material_kind(material_kind, filename=filename)
        source = _persist_source(
            uid=uid,
            payload=payload,
            date_folder=date_folder,
            topic_name=topic_name,
            material_kind=kind,
            inner_path=filename,
        )
        store.upsert_job(
            JobItem(
                id=f"job-{uuid.uuid4().hex[:10]}",
                kind="upload",
                status="done",
                message="강사 자료를 저장했습니다.",
                source_id=source.id,
                created_at=source.created_at,
                user_id=uid,
            )
        )
        return source

    @application.post("/api/sources/folder", response_model=FolderUploadResponse, status_code=201)
    async def upload_code_folder(
        files: Annotated[list[UploadFile], File()],
        user_id: Annotated[str | None, Form()] = None,
        topic: Annotated[str | None, Form()] = None,
        study_date: Annotated[str | None, Form()] = None,
        paths: Annotated[list[str] | str | None, Form()] = None,
    ) -> FolderUploadResponse:
        uid = require_user_id(user_id)
        if not files:
            raise HTTPException(status_code=400, detail="폴더에서 파일을 선택하세요.")
        if len(files) > MAX_FILES:
            raise HTTPException(
                status_code=400, detail=f"한 번에 {MAX_FILES}개까지만 올릴 수 있습니다."
            )

        try:
            date_folder = parse_study_date(study_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        path_values = _form_list(paths, len(files))
        collected: list[FolderEntry] = []
        total = 0
        for upload, raw_path in zip(files, path_values, strict=False):
            raw = (raw_path or upload.filename or "").strip()
            try:
                rel = strip_root_segment(normalize_relpath(raw))
                rel = normalize_relpath(rel)
            except ValueError:
                continue
            if should_skip_relpath(rel) or not is_code_folder_file(rel):
                continue
            payload = await upload.read()
            if not payload:
                continue
            if len(payload) > MAX_FILE_BYTES:
                raise HTTPException(
                    status_code=413, detail=f"{rel} 파일이 너무 큽니다. 파일당 2MB 이하만 받습니다."
                )
            total += len(payload)
            if total > MAX_FOLDER_BYTES:
                raise HTTPException(
                    status_code=413, detail="폴더 전체 크기는 40MB 이하여야 합니다."
                )
            collected.append(
                FolderEntry(path=rel, payload=payload, snippet=snippet_from_bytes(payload))
            )

        if not collected:
            raise HTTPException(
                status_code=400,
                detail="올릴 코드 파일이 없습니다. 의존성 폴더와 바이너리는 건너뜁니다.",
            )

        known = sorted(
            {
                item.topic
                for item in store.list_sources(material_kind="code")
                if item.topic and item.topic != "미분류"
            }
        )
        mapping, classified_by = classify_folder(collected, forced_topic=topic, known_topics=known)
        items = [
            _persist_source(
                uid=uid,
                payload=entry.payload,
                date_folder=date_folder,
                topic_name=mapping.get(entry.path) or heuristic_topic(entry.path),
                material_kind="code",
                inner_path=entry.path,
            )
            for entry in collected
        ]
        topics_used = sorted({item.topic for item in items})
        if classified_by == "gemini":
            message = (
                f"폴더 {len(items)}개 파일을 AI가 {len(topics_used)}개 주제로 나눠 저장했습니다."
            )
        elif classified_by == "topic":
            message = f"폴더 {len(items)}개 파일을 '{topics_used[0]}' 주제로 저장했습니다."
        else:
            message = f"폴더 {len(items)}개 파일을 경로 기준으로 {len(topics_used)}개 주제로 나눠 저장했습니다."
        store.upsert_job(
            JobItem(
                id=f"job-{uuid.uuid4().hex[:10]}",
                kind="upload",
                status="done",
                message=message,
                source_id=items[0].id,
                created_at=items[0].created_at,
                user_id=uid,
            )
        )
        return FolderUploadResponse(items=items, classified_by=classified_by, message=message)

    @application.get("/api/notes", response_model=list[NoteItem])
    def list_notes(user_id: str | None = None) -> list[NoteItem]:
        return store.list_notes(user_id=require_user_id(user_id))

    @application.post("/api/notes", response_model=NoteItem, status_code=201)
    def create_note(body: NoteCreateRequest | None = None) -> NoteItem:
        uid = require_user_id(body.user_id if body else None)
        title = (body.title if body and body.title else "새 노트").strip() or "새 노트"
        date_folder = today_folder()
        markdown = f"# {title}\n\n빈 노트입니다. 개인 작업 공간에서 수업 내용을 정리하세요.\n"
        _, note_rel = _write_note_file(uid, date_folder, title, markdown)
        note = NoteItem(
            id=f"note-{uuid.uuid4().hex[:10]}",
            title=title,
            preview="아직 본문이 없습니다. 수업 내용을 여기에 정리하세요.",
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
