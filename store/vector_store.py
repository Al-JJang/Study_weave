"""
공유 벡터 저장소.

합의 DB: PostgreSQL + pgvector

연동:
    쓰기 ← workers/parser/nodes.py (parse 후 upsert)
    읽기 → workers/parser/nodes.py retrieve_chunks_node → C analyze
    설정 ← config.DATABASE_URL
"""

from __future__ import annotations

from schemas.files import Chunk, RetrievedChunk


def initialize_vector_db() -> None:
    raise NotImplementedError("store: initialize_vector_db")


def upsert_chunks(request_id: str, chunks: list[Chunk]) -> None:
    raise NotImplementedError("store: upsert_chunks")


def retrieve_vector_documents(
    query: str,
    request_id: str,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    raise NotImplementedError("store: retrieve_vector_documents")
