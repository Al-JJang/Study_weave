"""프로세스 메모리 저장소. DB가 아직 없어도 UI가 동작하게 한다."""

from __future__ import annotations

from threading import Lock

from api.models import JobItem, NoteItem, SourceItem

_lock = Lock()
_sources: dict[str, SourceItem] = {}
_notes: dict[str, NoteItem] = {}
_jobs: dict[str, JobItem] = {}


def reset(*, seed: bool = False) -> None:
    with _lock:
        _sources.clear()
        _notes.clear()
        _jobs.clear()
    if seed:
        seed_demo()


def seed_demo() -> None:
    """팀이 첫 화면을 볼 수 있게 mock 소스/노트 한 건씩 넣는다."""
    source = SourceItem(
        id="src-demo-pdf",
        filename="langgraph_agent_guide.pdf",
        source_type="pdf",
        size_bytes=248_832,
        created_at="2026-09-28T09:00:00+00:00",
        status="ready",
        user_id="seoyoung",
        date_folder="2026-09-28",
        relative_path="seoyoung/2026-09-28/langgraph_agent_guide.pdf",
        note_id="note-demo-001",
    )
    note = NoteItem(
        id="note-demo-001",
        title="Agent Loop 학습 노트",
        preview="@tool 데코레이터와 Agent Loop 패턴을 개념·코드·퀴즈로 정리한 샘플 노트입니다.",
        markdown=(
            "# Agent Loop 학습 노트\n\n"
            "이 노트는 그래프가 mock일 때 UI가 채워 보이는지 확인하기 위한 샘플입니다.\n\n"
            "## 개념\n"
            "- `@tool` 데코레이터는 일반 함수를 LLM이 호출 가능한 Tool로 바꿉니다.\n"
            "- Agent Loop는 agent와 tools를 순환시켜 Tool 결과를 다시 판단에 넣습니다.\n\n"
            "## 다음에 할 일\n"
            "소스를 업로드하면 같은 형식으로 노트가 추가됩니다.\n"
        ),
        source_ids=["src-demo-pdf"],
        created_at="2026-09-28T09:05:00+00:00",
        status="ready",
        user_id="seoyoung",
        date_folder="2026-09-28",
        relative_path="seoyoung/2026-09-28/Agent_Loop_학습_노트.md",
    )
    job = JobItem(
        id="job-demo-001",
        kind="upload",
        status="done",
        message="샘플 소스로 노트를 만들었습니다.",
        source_id=source.id,
        note_id=note.id,
        created_at="2026-09-28T09:05:00+00:00",
        user_id="seoyoung",
    )
    with _lock:
        _sources[source.id] = source
        _notes[note.id] = note
        _jobs[job.id] = job


def list_sources(*, user_id: str) -> list[SourceItem]:
    with _lock:
        items = [item for item in _sources.values() if item.user_id == user_id]
        return sorted(items, key=lambda item: (item.date_folder, item.filename), reverse=True)


def get_source(source_id: str) -> SourceItem | None:
    with _lock:
        return _sources.get(source_id)


def upsert_source(item: SourceItem) -> SourceItem:
    with _lock:
        _sources[item.id] = item
        return item


def list_notes(*, user_id: str) -> list[NoteItem]:
    with _lock:
        items = [item for item in _notes.values() if item.user_id == user_id]
        return sorted(items, key=lambda item: item.created_at, reverse=True)


def get_note(note_id: str) -> NoteItem | None:
    with _lock:
        return _notes.get(note_id)


def upsert_note(item: NoteItem) -> NoteItem:
    with _lock:
        _notes[item.id] = item
        return item


def list_jobs(*, user_id: str | None = None) -> list[JobItem]:
    with _lock:
        items = list(_jobs.values())
        if user_id is not None:
            items = [item for item in items if item.user_id == user_id]
        return sorted(items, key=lambda item: item.created_at, reverse=True)


def upsert_job(item: JobItem) -> JobItem:
    with _lock:
        _jobs[item.id] = item
        return item
