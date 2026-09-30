"""사용자별 개인 책상 — 섹션 추가/이름변경/삭제, 항목 이동."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr("api.main.UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr("api.main.NOTES_DIR", tmp_path / "notes")
    monkeypatch.setattr("api.desk.DESK_DIR", tmp_path / "desks")
    application = create_app(seed=False)
    with TestClient(application) as test_client:
        yield test_client


def test_empty_desk(client: TestClient) -> None:
    body = client.get("/api/desk", params={"user_id": "donggyu"}).json()
    assert body["user_id"] == "donggyu"
    assert body["user_name"] == "동규"
    assert body["sections"] == []
    assert body["unfiled"] == []


def test_section_crud_and_move(client: TestClient, tmp_path: Path) -> None:
    note = client.post("/api/notes", json={"title": "복습", "user_id": "donggyu"}).json()
    created = client.post("/api/desk/sections", json={"user_id": "donggyu", "title": "중간고사"})
    assert created.status_code == 201
    section_id = created.json()["sections"][0]["id"]
    assert created.json()["unfiled"][0]["id"] == note["id"]

    moved = client.post(
        "/api/desk/move",
        json={
            "user_id": "donggyu",
            "kind": "note",
            "item_id": note["id"],
            "section_id": section_id,
        },
    )
    assert moved.status_code == 200
    assert moved.json()["unfiled"] == []
    assert moved.json()["sections"][0]["items"][0]["id"] == note["id"]

    renamed = client.patch(
        f"/api/desk/sections/{section_id}",
        json={"user_id": "donggyu", "title": "기말고사"},
    )
    assert renamed.json()["sections"][0]["title"] == "기말고사"

    desk_file = tmp_path / "desks" / "donggyu" / "desk.json"
    assert desk_file.is_file()
    assert "기말고사" in desk_file.read_text(encoding="utf-8")

    other = client.get("/api/desk", params={"user_id": "seoyoung"}).json()
    assert other["sections"] == []

    deleted = client.delete(f"/api/desk/sections/{section_id}", params={"user_id": "donggyu"})
    assert deleted.status_code == 200
    assert deleted.json()["sections"] == []
    assert deleted.json()["unfiled"][0]["id"] == note["id"]


def test_cannot_move_other_users_note(client: TestClient) -> None:
    note = client.post("/api/notes", json={"title": "서영 노트", "user_id": "seoyoung"}).json()
    section = client.post(
        "/api/desk/sections", json={"user_id": "donggyu", "title": "내 폴더"}
    ).json()
    response = client.post(
        "/api/desk/move",
        json={
            "user_id": "donggyu",
            "kind": "note",
            "item_id": note["id"],
            "section_id": section["sections"][0]["id"],
        },
    )
    assert response.status_code == 404
