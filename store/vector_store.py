"""
공유 벡터 저장소.

합의 DB: PostgreSQL + pgvector
강의 패턴: day1 chromadb / day3 langchain_chroma.Chroma
  → 같은 함수 이름(initialize / upsert / retrieve)으로 구현하면 B·C 가 강의 코드를 옮기기 쉽다.

연동:
    쓰기 ← workers/parser/nodes.py (parse 후 upsert)
    읽기 → workers/parser/nodes.py retrieve_chunks_node → C analyze
    설정 ← config.VECTOR_BACKEND, DATABASE_URL, CHROMA_DIR
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
