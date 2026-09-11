"""Mock 데이터가 스키마 제약(출처 필수, 청크 id 존재 등)과 어긋나지 않는지 확인."""

from __future__ import annotations

from mocks.data import (
    MOCK_CODE_ANALYSIS,
    MOCK_CONCEPT_SUMMARY,
    MOCK_CROSS_REFERENCES,
    MOCK_FILES,
    MOCK_PARSED_CHUNKS,
    MOCK_QUIZ_ITEMS,
    MOCK_RETRIEVED_CHUNKS,
    MOCK_TROUBLESHOOTING,
)


def test_mock_collections_are_not_empty():
    assert MOCK_FILES
    assert MOCK_PARSED_CHUNKS
    assert MOCK_RETRIEVED_CHUNKS
    assert MOCK_CONCEPT_SUMMARY
    assert MOCK_CODE_ANALYSIS
    assert MOCK_CROSS_REFERENCES
    assert MOCK_TROUBLESHOOTING
    assert MOCK_QUIZ_ITEMS


def test_retrieved_chunks_reference_existing_chunk_ids():
    known_ids = {chunk.chunk_id for chunk in MOCK_PARSED_CHUNKS}
    for chunk in MOCK_RETRIEVED_CHUNKS:
        assert chunk.chunk_id in known_ids


def test_mcq_answer_is_one_of_its_options():
    for item in MOCK_QUIZ_ITEMS:
        if item.quiz_type == "mcq":
            assert item.answer in item.options
