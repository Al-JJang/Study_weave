"""사용자별 개인 책상. data/desks/{user_id}/desk.json 에 저장한다."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from threading import Lock

from fastapi import HTTPException

import api.store as store
from api.models import (
    DeskItem,
    DeskItemRef,
    DeskMoveRequest,
    DeskRecord,
    DeskResponse,
    DeskSection,
    DeskSectionCreate,
    DeskSectionRecord,
    DeskSectionRename,
)
from api.users import USER_NAMES, require_user_id
from config import DATA_DIR

DESK_DIR = DATA_DIR / "desks"
_lock = Lock()


def _desk_path(user_id: str) -> Path:
    return DESK_DIR / user_id / "desk.json"


def _empty(user_id: str) -> DeskRecord:
    return DeskRecord(user_id=user_id, sections=[])


def load_record(user_id: str) -> DeskRecord:
    path = _desk_path(user_id)
    if not path.is_file():
        return _empty(user_id)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return DeskRecord.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValueError):
        return _empty(user_id)


def save_record(record: DeskRecord) -> None:
    path = _desk_path(record.user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=2), encoding="utf-8")


def _as_item(kind: str, item_id: str, user_id: str) -> DeskItem | None:
    if kind == "note":
        note = store.get_note(item_id)
        if note is None or note.user_id != user_id:
            return None
        return DeskItem(
            kind="note",
            id=note.id,
            title=note.title,
            href=f"/notes/{note.id}",
            preview=note.preview,
        )
    source = store.get_source(item_id)
    if source is None or source.user_id != user_id:
        return None
    return DeskItem(
        kind="source",
        id=source.id,
        title=source.filename,
        href="/sources",
        preview=source.relative_path,
    )


def _resolve_items(refs: list[DeskItemRef], user_id: str) -> list[DeskItem]:
    items: list[DeskItem] = []
    for ref in refs:
        resolved = _as_item(ref.kind, ref.id, user_id)
        if resolved is not None:
            items.append(resolved)
    return items


def build_response(user_id: str) -> DeskResponse:
    uid = require_user_id(user_id)
    with _lock:
        record = load_record(uid)
    placed: set[tuple[str, str]] = set()
    sections: list[DeskSection] = []
    kept_sections: list[DeskSectionRecord] = []
    dirty = False
    for section in record.sections:
        live_refs: list[DeskItemRef] = []
        for ref in section.items:
            key = (ref.kind, ref.id)
            if key in placed:
                dirty = True
                continue
            resolved = _as_item(ref.kind, ref.id, uid)
            if resolved is None:
                dirty = True
                continue
            placed.add(key)
            live_refs.append(ref)
        if live_refs != section.items:
            dirty = True
        kept_sections.append(DeskSectionRecord(id=section.id, title=section.title, items=live_refs))
        sections.append(
            DeskSection(id=section.id, title=section.title, items=_resolve_items(live_refs, uid))
        )

    unfiled: list[DeskItem] = []
    for note in store.list_notes(user_id=uid):
        if ("note", note.id) not in placed:
            item = _as_item("note", note.id, uid)
            if item:
                unfiled.append(item)
    for source in store.list_sources(user_id=uid):
        if ("source", source.id) not in placed:
            item = _as_item("source", source.id, uid)
            if item:
                unfiled.append(item)

    if dirty:
        with _lock:
            save_record(DeskRecord(user_id=uid, sections=kept_sections))

    return DeskResponse(
        user_id=uid,
        user_name=USER_NAMES[uid],
        sections=sections,
        unfiled=unfiled,
    )


def create_section(body: DeskSectionCreate) -> DeskResponse:
    uid = require_user_id(body.user_id)
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="섹션 이름을 입력하세요.")
    with _lock:
        record = load_record(uid)
        record.sections.append(
            DeskSectionRecord(id=f"sec-{uuid.uuid4().hex[:10]}", title=title, items=[])
        )
        save_record(record)
    return build_response(uid)


def rename_section(section_id: str, body: DeskSectionRename) -> DeskResponse:
    uid = require_user_id(body.user_id)
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="섹션 이름을 입력하세요.")
    with _lock:
        record = load_record(uid)
        target = next((section for section in record.sections if section.id == section_id), None)
        if target is None:
            raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다.")
        target.title = title
        save_record(record)
    return build_response(uid)


def delete_section(section_id: str, user_id: str | None) -> DeskResponse:
    uid = require_user_id(user_id)
    with _lock:
        record = load_record(uid)
        before = len(record.sections)
        record.sections = [section for section in record.sections if section.id != section_id]
        if len(record.sections) == before:
            raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다.")
        save_record(record)
    return build_response(uid)


def move_item(body: DeskMoveRequest) -> DeskResponse:
    uid = require_user_id(body.user_id)
    if _as_item(body.kind, body.item_id, uid) is None:
        raise HTTPException(status_code=404, detail="이 사용자의 노트나 소스가 아닙니다.")
    ref = DeskItemRef(kind=body.kind, id=body.item_id)
    with _lock:
        record = load_record(uid)
        for section in record.sections:
            section.items = [
                item for item in section.items if not (item.kind == ref.kind and item.id == ref.id)
            ]
        if body.section_id is not None:
            target = next(
                (section for section in record.sections if section.id == body.section_id), None
            )
            if target is None:
                raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다.")
            target.items.append(ref)
        save_record(record)
    return build_response(uid)
