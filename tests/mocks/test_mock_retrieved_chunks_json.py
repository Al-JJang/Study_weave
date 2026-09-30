"""mock_retrieved_chunks.json 이 RetrievedChunk 스키마와 MOCK_RETRIEVED_CHUNKS 와 어긋나지 않는지 확인."""

from __future__ import annotations

from mocks.data import (
    MOCK_PARSED_CHUNKS,
    MOCK_RETRIEVED_CHUNKS,
    MOCK_RETRIEVED_CHUNKS_JSON_PATH,
    load_mock_retrieved_chunks_json,
)


def test_json_fixture_file_exists():
    assert MOCK_RETRIEVED_CHUNKS_JSON_PATH.exists()
    assert MOCK_RETRIEVED_CHUNKS_JSON_PATH.name == "mock_retrieved_chunks.json"


def test_json_fixture_parses_into_retrieved_chunks():
    chunks = load_mock_retrieved_chunks_json()
    assert chunks
    for chunk in chunks:
        assert chunk.chunk_id
        assert chunk.distance is not None
        assert chunk.vector_rank is not None
        assert chunk.retrieval_sources


def test_json_fixture_matches_mock_retrieved_chunks_in_python():
    chunks = load_mock_retrieved_chunks_json()
    assert [c.model_dump() for c in chunks] == [c.model_dump() for c in MOCK_RETRIEVED_CHUNKS]


def test_json_fixture_references_existing_chunk_ids():
    known_ids = {chunk.chunk_id for chunk in MOCK_PARSED_CHUNKS}
    for chunk in load_mock_retrieved_chunks_json():
        assert chunk.chunk_id in known_ids
