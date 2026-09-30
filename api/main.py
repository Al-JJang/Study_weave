"""StudyWeave AI FastAPI 앱.

제공 엔드포인트:
    GET  /api/health
    GET  /api/sources
    POST /api/sources          파일 업로드
    GET  /api/notes
    POST /api/notes            빈 노트 생성
    GET  /api/notes/{note_id}
    GET  /api/jobs
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import api.store as store
from api.models import (
    HealthResponse,
    JobItem,
    NoteCreateRequest,
    NoteItem,
    SourceItem,
    SourceKind,
)
from api.pipeline import graph_available, try_mock_markdown
from config import DATA_DIR

UPLOAD_DIR = DATA_DIR / "uploads"
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


def create_app(*, seed: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
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

    @application.get("/api/sources", response_model=list[SourceItem])
    def list_sources() -> list[SourceItem]:
        return store.list_sources()

    @application.post("/api/sources", response_model=SourceItem, status_code=201)
    async def upload_source(file: Annotated[UploadFile, File()]) -> SourceItem:
        filename = (file.filename or "").strip()
        if not filename:
            raise HTTPException(status_code=400, detail="파일 이름이 필요합니다.")

        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="빈 파일은 업로드할 수 없습니다.")
        if len(payload) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="파일 크기는 20MB 이하여야 합니다.")

        source_id = f"src-{uuid.uuid4().hex[:10]}"
        safe_name = Path(filename).name
        dest = UPLOAD_DIR / f"{source_id}_{safe_name}"
        dest.write_bytes(payload)

        created = _now()
        source = SourceItem(
            id=source_id,
            filename=safe_name,
            source_type=_source_type(safe_name),
            size_bytes=len(payload),
            created_at=created,
            status="processing",
        )
        store.upsert_source(source)

        job = JobItem(
            id=f"job-{uuid.uuid4().hex[:10]}",
            kind="upload",
            status="running",
            message="파일을 저장했습니다. 학습 노트를 준비합니다.",
            source_id=source_id,
            created_at=created,
        )
        store.upsert_job(job)

        markdown = try_mock_markdown()
        if markdown:
            title = _title_from_markdown(markdown, Path(safe_name).stem)
            note = NoteItem(
                id=f"note-{uuid.uuid4().hex[:10]}",
                title=title,
                preview=_preview(markdown, title),
                markdown=markdown,
                source_ids=[source_id],
                created_at=_now(),
                status="ready",
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
            note = NoteItem(
                id=f"note-{uuid.uuid4().hex[:10]}",
                title=Path(safe_name).stem,
                preview="그래프가 아직 없어 placeholder 노트를 만들었습니다.",
                markdown=(
                    f"# {Path(safe_name).stem}\n\n"
                    "업로드는 완료됐습니다. 분석 그래프가 연결되면 이 자리에 "
                    "개념·코드·퀴즈 노트가 채워집니다.\n"
                ),
                source_ids=[source_id],
                created_at=_now(),
                status="draft",
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
    def list_notes() -> list[NoteItem]:
        return store.list_notes()

    @application.post("/api/notes", response_model=NoteItem, status_code=201)
    def create_note(body: NoteCreateRequest | None = None) -> NoteItem:
        title = (body.title if body and body.title else "새 노트").strip() or "새 노트"
        note = NoteItem(
            id=f"note-{uuid.uuid4().hex[:10]}",
            title=title,
            preview="아직 본문이 없습니다. 소스를 올리면 학습 노트가 채워집니다.",
            markdown=(
                f"# {title}\n\n"
                "빈 노트입니다. 대시보드에서 소스를 업로드하면 분석 결과가 이 형식으로 쌓입니다.\n"
            ),
            source_ids=[],
            created_at=_now(),
            status="draft",
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
    def list_jobs() -> list[JobItem]:
        return store.list_jobs()

    return application


app = create_app(seed=True)
