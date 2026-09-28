"""Chunk 규격 정의 및 DB 적재: store.vector_store 단위 테스트 (Postgres/임베딩 모두 mock)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from pgvector import Vector

import config
from schemas.files import Chunk
from store import vector_store


class FakeCursor:
    """psycopg Cursor 흉내. execute 호출을 기록하고 미리 정해둔 rows를 돌려준다."""

    def __init__(
        self,
        rows: list[tuple[Any, ...]] | None = None,
        columns: list[str] | None = None,
    ) -> None:
        self.queries: list[tuple[str, dict[str, Any] | None]] = []
        self._rows = rows or []
        self.description = [SimpleNamespace(name=name) for name in (columns or [])]

    def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        self.queries.append((query, params))

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self._rows

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None


class FakeConnection:
    """psycopg Connection 흉내. cursor()는 항상 같은 FakeCursor를 반환한다."""

    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor
        self.committed = False

    def cursor(self, **_kwargs: Any) -> FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def __enter__(self) -> FakeConnection:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None


class FakeEmbeddings:
    """config.get_embeddings() 대체. 텍스트 길이를 벡터 값으로 써서 결정론적으로 만든다."""

    def __init__(self, dimension: int = 4) -> None:
        self.dimension = dimension
        self.document_calls: list[list[str]] = []
        self.query_calls: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_calls.append(list(texts))
        return [[float(len(text))] * self.dimension for text in texts]

    def embed_query(self, text: str) -> list[float]:
        self.query_calls.append(text)
        return [float(len(text))] * self.dimension


def _patch_connect(monkeypatch: pytest.MonkeyPatch, conn: FakeConnection) -> None:
    monkeypatch.setattr(vector_store.psycopg, "connect", lambda *_a, **_kw: conn)
    monkeypatch.setattr(vector_store, "register_vector", lambda _conn: None)


def _sample_chunks() -> list[Chunk]:
    return [
        Chunk(
            chunk_id="req-1:file.py:chunk:0000",
            document_id="req-1:file.py",
            source_type="code",
            content="def foo():\n    return 1",
            chunk_index=0,
            start_line=1,
            end_line=2,
        ),
        Chunk(
            chunk_id="req-1:file.py:chunk:0001",
            document_id="req-1:file.py",
            source_type="code",
            content="def bar():\n    return 2",
            chunk_index=1,
            start_line=4,
            end_line=5,
        ),
    ]


def test_initialize_vector_db_creates_extension_table_and_indexes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    _patch_connect(monkeypatch, conn)

    vector_store.initialize_vector_db()

    executed = [query for query, _ in cursor.queries]
    assert any("CREATE EXTENSION IF NOT EXISTS vector" in q for q in executed)
    assert any("CREATE TABLE IF NOT EXISTS studywave_chunks" in q for q in executed)
    assert any(f"VECTOR({config.EMBEDDING_DIMENSION})" in q for q in executed)
    assert any("idx_studywave_chunks_request_id" in q for q in executed)
    assert any("idx_studywave_chunks_embedding" in q for q in executed)
    assert conn.committed


def test_upsert_chunks_does_nothing_for_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail_connect(*_a: object, **_kw: object) -> None:
        raise AssertionError("빈 리스트인데 DB에 연결하면 안 된다")

    monkeypatch.setattr(vector_store.psycopg, "connect", _fail_connect)

    vector_store.upsert_chunks("req-1", [])


def test_upsert_chunks_embeds_content_and_inserts_each_chunk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    _patch_connect(monkeypatch, conn)
    fake_embeddings = FakeEmbeddings()
    monkeypatch.setattr(config, "get_embeddings", lambda: fake_embeddings)

    chunks = _sample_chunks()
    vector_store.upsert_chunks("req-1", chunks)

    assert fake_embeddings.document_calls == [[chunk.content for chunk in chunks]]
    insert_queries = [(q, p) for q, p in cursor.queries if "INSERT INTO" in q]
    assert len(insert_queries) == 2
    assert "ON CONFLICT (chunk_id) DO UPDATE" in insert_queries[0][0]

    first_params = insert_queries[0][1]
    assert first_params["chunk_id"] == chunks[0].chunk_id
    assert first_params["request_id"] == "req-1"
    assert first_params["document_id"] == chunks[0].document_id
    assert first_params["source_type"] == "code"
    assert first_params["start_line"] == 1
    assert first_params["end_line"] == 2
    expected_vector = Vector([float(len(chunks[0].content))] * fake_embeddings.dimension)
    assert first_params["embedding"] == expected_vector
    assert conn.committed


def test_retrieve_vector_documents_filters_by_similarity_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    columns = [
        "chunk_id",
        "document_id",
        "source_type",
        "content",
        "chunk_index",
        "page_number",
        "start_line",
        "end_line",
        "distance",
    ]
    rows = [
        ("req-1:a.py:chunk:0000", "req-1:a.py", "code", "def a(): pass", 0, None, 1, 1, 0.1),
        ("req-1:b.py:chunk:0000", "req-1:b.py", "code", "def b(): pass", 0, None, 1, 1, 0.9),
    ]
    cursor = FakeCursor(rows=rows, columns=columns)
    conn = FakeConnection(cursor)
    _patch_connect(monkeypatch, conn)
    fake_embeddings = FakeEmbeddings()
    monkeypatch.setattr(config, "get_embeddings", lambda: fake_embeddings)
    monkeypatch.setattr(config, "SIMILARITY_THRESHOLD", 0.6)

    results = vector_store.retrieve_vector_documents("agent tool 사용법", "req-1")

    assert fake_embeddings.query_calls == ["agent tool 사용법"]
    select_query, params = cursor.queries[0]
    assert "WHERE request_id = %(request_id)s" in select_query
    assert params["request_id"] == "req-1"
    assert params["top_k"] == config.VECTOR_TOP_K

    assert len(results) == 1
    assert results[0].chunk_id == "req-1:a.py:chunk:0000"
    assert results[0].distance == 0.1
    assert results[0].vector_rank == 1
    assert results[0].retrieval_sources == ["vector"]


def test_retrieve_vector_documents_uses_custom_top_k(monkeypatch: pytest.MonkeyPatch) -> None:
    cursor = FakeCursor(rows=[], columns=[])
    conn = FakeConnection(cursor)
    _patch_connect(monkeypatch, conn)
    monkeypatch.setattr(config, "get_embeddings", lambda: FakeEmbeddings())

    results = vector_store.retrieve_vector_documents("query", "req-1", top_k=2)

    assert results == []
    _, params = cursor.queries[0]
    assert params["top_k"] == 2


def test_retrieve_vector_documents_ranks_multiple_matches_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    columns = [
        "chunk_id",
        "document_id",
        "source_type",
        "content",
        "chunk_index",
        "page_number",
        "start_line",
        "end_line",
        "distance",
    ]
    rows = [
        ("req-1:a.py:chunk:0000", "req-1:a.py", "code", "def a(): pass", 0, None, 1, 1, 0.05),
        ("req-1:b.py:chunk:0000", "req-1:b.py", "code", "def b(): pass", 0, None, 1, 1, 0.2),
    ]
    cursor = FakeCursor(rows=rows, columns=columns)
    conn = FakeConnection(cursor)
    _patch_connect(monkeypatch, conn)
    monkeypatch.setattr(config, "get_embeddings", lambda: FakeEmbeddings())
    monkeypatch.setattr(config, "SIMILARITY_THRESHOLD", 0.6)

    results = vector_store.retrieve_vector_documents("query", "req-1")

    assert [chunk.vector_rank for chunk in results] == [1, 2]
    assert [chunk.chunk_id for chunk in results] == [
        "req-1:a.py:chunk:0000",
        "req-1:b.py:chunk:0000",
    ]
