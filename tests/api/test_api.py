"""FastAPI 뼈대 — 헬스체크, 업로드, 노트/작업 목록."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr("api.main.UPLOAD_DIR", tmp_path / "uploads")
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


def test_lists_start_empty(client: TestClient) -> None:
    assert client.get("/api/sources").json() == []
    assert client.get("/api/notes").json() == []
    assert client.get("/api/jobs").json() == []


def test_upload_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        "/api/sources",
        files={"file": ("notes.txt", b"", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_creates_source_note_and_job(client: TestClient) -> None:
    response = client.post(
        "/api/sources",
        files={"file": ("agentEx4.py", b"print('hello')\n", "text/x-python")},
    )
    assert response.status_code == 201
    source = response.json()
    assert source["filename"] == "agentEx4.py"
    assert source["source_type"] == "code"
    assert source["status"] == "ready"
    assert source["note_id"]

    sources = client.get("/api/sources").json()
    assert len(sources) == 1

    notes = client.get("/api/notes").json()
    assert len(notes) == 1
    note = client.get(f"/api/notes/{notes[0]['id']}").json()
    assert "agentEx4" in note["title"] or note["markdown"]

    jobs = client.get("/api/jobs").json()
    assert jobs
    assert jobs[0]["kind"] == "upload"
    assert jobs[0]["status"] == "done"


def test_create_blank_note(client: TestClient) -> None:
    response = client.post("/api/notes", json={"title": "복습 메모"})
    assert response.status_code == 201
    note = response.json()
    assert note["title"] == "복습 메모"
    assert note["status"] == "draft"
    assert client.get(f"/api/notes/{note['id']}").status_code == 200


def test_missing_note_is_404(client: TestClient) -> None:
    response = client.get("/api/notes/does-not-exist")
    assert response.status_code == 404


def test_seeded_app_has_demo_rows() -> None:
    application = create_app(seed=True)
    with TestClient(application) as test_client:
        assert test_client.get("/api/sources").json()
        assert test_client.get("/api/notes").json()
        assert test_client.get("/api/jobs").json()
