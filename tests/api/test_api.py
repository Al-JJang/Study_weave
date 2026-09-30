"""FastAPI 뼈대 — 헬스체크, 사용자별 업로드, 노트, 챗봇."""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.paths import parse_study_date, sanitize_filename
from api.users import MISSING_USER_DETAIL


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr("api.main.UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr("api.main.NOTES_DIR", tmp_path / "notes")
    monkeypatch.setattr("api.desk.DESK_DIR", tmp_path / "desks")
    application = create_app(seed=False)
    with TestClient(application) as test_client:
        yield test_client


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "studyweave-ai"
    assert "graph_available" in body


def test_users_are_the_four_teammates(client: TestClient) -> None:
    body = client.get("/api/users").json()
    assert [row["name"] for row in body] == ["서영", "송주", "새결", "동규"]


def test_lists_require_user_id(client: TestClient) -> None:
    response = client.get("/api/sources")
    assert response.status_code == 400
    assert response.json()["detail"] == MISSING_USER_DETAIL


def test_lists_start_empty(client: TestClient) -> None:
    assert client.get("/api/sources", params={"user_id": "donggyu"}).json() == []
    assert client.get("/api/notes", params={"user_id": "donggyu"}).json() == []
    assert client.get("/api/jobs", params={"user_id": "donggyu"}).json() == []


def test_upload_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        "/api/sources",
        data={"user_id": "donggyu"},
        files={"file": ("notes.txt", b"", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_rejects_missing_user(client: TestClient) -> None:
    response = client.post(
        "/api/sources",
        files={"file": ("notes.txt", b"hi\n", "text/plain")},
    )
    assert response.status_code == 400


def test_sanitize_filename_strips_paths() -> None:
    assert sanitize_filename("../secret.pdf") == "secret.pdf"
    assert sanitize_filename("my file (1).PY") == "my_file_1.py"
    assert parse_study_date("7/21") == "2026-07-21"
    assert parse_study_date("2026-09-30") == "2026-09-30"


def test_upload_creates_user_date_folder(client: TestClient, tmp_path: Path) -> None:
    response = client.post(
        "/api/sources",
        data={"user_id": "donggyu"},
        files={"file": ("agentEx4.py", b"print('hello')\n", "text/x-python")},
    )
    assert response.status_code == 201
    source = response.json()
    assert source["filename"] == "agentEx4.py"
    assert source["source_type"] == "code"
    assert source["status"] == "ready"
    assert source["user_id"] == "donggyu"
    assert source["note_id"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", source["date_folder"])
    assert source["relative_path"] == f"donggyu/{source['date_folder']}/미분류/{source['filename']}"
    assert source["topic"] == "미분류"
    saved = tmp_path / "uploads" / source["relative_path"]
    assert saved.is_file()
    assert saved.read_bytes() == b"print('hello')\n"

    notes = client.get("/api/notes", params={"user_id": "donggyu"}).json()
    assert len(notes) == 1
    note_path = tmp_path / "notes" / notes[0]["relative_path"]
    assert note_path.is_file()

    other = client.get("/api/notes", params={"user_id": "seoyoung"}).json()
    assert other == []


def test_same_day_duplicate_filename_gets_suffix(client: TestClient) -> None:
    payload = {"user_id": "songju"}
    first = client.post(
        "/api/sources",
        data=payload,
        files={"file": ("slide.pdf", b"%PDF-1.4 demo", "application/pdf")},
    )
    second = client.post(
        "/api/sources",
        data=payload,
        files={"file": ("slide.pdf", b"%PDF-1.4 copy", "application/pdf")},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["filename"] == "slide.pdf"
    assert second.json()["filename"] == "slide-2.pdf"
    assert first.json()["date_folder"] == second.json()["date_folder"]


def test_upload_classifies_by_topic_and_date(client: TestClient, tmp_path: Path) -> None:
    response = client.post(
        "/api/sources",
        data={"user_id": "donggyu", "topic": "LangGraph", "study_date": "7/21"},
        files={"file": ("agentEx4.py", b"print('loop')\n", "text/x-python")},
    )
    assert response.status_code == 201
    source = response.json()
    assert source["topic"] == "LangGraph"
    assert source["date_folder"] == "2026-07-21"
    assert source["relative_path"] == "donggyu/2026-07-21/LangGraph/agentEx4.py"
    assert (tmp_path / "uploads" / source["relative_path"]).is_file()


def test_upload_rejects_bad_date(client: TestClient) -> None:
    response = client.post(
        "/api/sources",
        data={"user_id": "donggyu", "topic": "RAG", "study_date": "어제"},
        files={"file": ("notes.txt", b"hi\n", "text/plain")},
    )
    assert response.status_code == 400


def test_create_blank_note_in_user_folder(client: TestClient, tmp_path: Path) -> None:
    response = client.post("/api/notes", json={"title": "복습 메모", "user_id": "saegyeol"})
    assert response.status_code == 201
    note = response.json()
    assert note["title"] == "복습 메모"
    assert note["status"] == "draft"
    assert note["user_id"] == "saegyeol"
    assert (tmp_path / "notes" / note["relative_path"]).is_file()
    assert client.get(f"/api/notes/{note['id']}").status_code == 200
    assert client.get("/api/notes", params={"user_id": "donggyu"}).json() == []


def test_missing_note_is_404(client: TestClient) -> None:
    response = client.get("/api/notes/does-not-exist")
    assert response.status_code == 404


def test_seeded_app_has_demo_rows_for_seoyoung_only() -> None:
    application = create_app(seed=True)
    with TestClient(application) as test_client:
        assert test_client.get("/api/sources", params={"user_id": "seoyoung"}).json()
        assert test_client.get("/api/notes", params={"user_id": "seoyoung"}).json()
        assert test_client.get("/api/jobs", params={"user_id": "seoyoung"}).json()
        assert test_client.get("/api/sources", params={"user_id": "donggyu"}).json() == []


def test_chat_requires_gemini_key(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("config.GEMINI_API_KEY", None)
    response = client.post("/api/chat", json={"user_id": "donggyu", "message": "요약해 줘"})
    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]


def test_chat_streams_with_note_context(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("config.GEMINI_API_KEY", "test-key")

    class FakeModel:
        def stream(self, messages: object):
            joined = str(messages)
            assert "복습 메모" in joined or "빈 노트" in joined
            yield SimpleNamespace(content="노트에 ")
            yield SimpleNamespace(content="퀴즈가 있습니다.")

    monkeypatch.setattr("api.chat.get_chat_model", lambda **_: FakeModel())
    created = client.post("/api/notes", json={"title": "복습 메모", "user_id": "donggyu"})
    assert created.status_code == 201

    response = client.post("/api/chat", json={"user_id": "donggyu", "message": "요약해 줘"})
    assert response.status_code == 200
    assert "노트에 " in response.text
    assert "퀴즈가 있습니다." in response.text
    assert "[DONE]" in response.text
