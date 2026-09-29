"""
공유 벡터 저장소.

합의 DB: PostgreSQL + pgvector

연동:
    쓰기 ← workers/parser/nodes.py (parse 후 upsert)
    읽기 → workers/parser/nodes.py retrieve_chunks_node → C analyze
    설정 ← config.DATABASE_URL, config.EMBEDDING_DIMENSION, config.VECTOR_TOP_K,
           config.SIMILARITY_THRESHOLD, config.get_embeddings()

테이블 DDL은 db/init.sql과 동일하게 유지한다(컬럼을 바꾸면 둘 다 바꿀 것).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector

import config
from schemas.files import Chunk, RetrievedChunk

TABLE_NAME = config.COLLECTION_NAME


@contextmanager
def _connect() -> Iterator[psycopg.Connection]:
    """pgvector 타입이 등록된 커넥션. 커밋/커넥션 종료까지 책임진다."""
    with psycopg.connect(config.DATABASE_URL) as conn:
        register_vector(conn)
        yield conn


def initialize_vector_db() -> None:
    """pgvector 확장과 `studywave_chunks` 테이블/인덱스를 만든다.

    이미 존재하면 아무 것도 하지 않는다(멱등). db/init.sql과 동일한 DDL.
    """
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                chunk_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                source_type TEXT NOT NULL CHECK (source_type IN ('pdf', 'code')),
                chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
                content TEXT NOT NULL,
                page_number INTEGER CHECK (page_number IS NULL OR page_number >= 1),
                start_line INTEGER CHECK (start_line IS NULL OR start_line >= 1),
                end_line INTEGER CHECK (end_line IS NULL OR end_line >= 1),
                embedding VECTOR({config.EMBEDDING_DIMENSION}) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cur.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_request_id ON {TABLE_NAME} (request_id)"
        )
        cur.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_embedding "
            f"ON {TABLE_NAME} USING hnsw (embedding vector_cosine_ops)"
        )
        conn.commit()


def upsert_chunks(request_id: str, chunks: list[Chunk]) -> None:
    """chunks를 임베딩해서 적재한다. 같은 chunk_id면 내용/임베딩을 갱신한다.

    Args:
        request_id: 이 배치가 속한 업로드 요청 ID. retrieve 시 필터 기준이 된다.
        chunks: parse_files_node가 만든 Chunk 리스트. 비어 있으면 아무 것도 하지 않는다.
    """
    if not chunks:
        return

    embeddings = config.get_embeddings()
    vectors = embeddings.embed_documents([chunk.content for chunk in chunks])

    with _connect() as conn, conn.cursor() as cur:
        for chunk, vector in zip(chunks, vectors, strict=True):
            cur.execute(
                f"""
                INSERT INTO {TABLE_NAME} (
                    chunk_id, request_id, document_id, source_type,
                    chunk_index, content, page_number, start_line, end_line, embedding
                )
                VALUES (
                    %(chunk_id)s, %(request_id)s, %(document_id)s, %(source_type)s,
                    %(chunk_index)s, %(content)s, %(page_number)s, %(start_line)s,
                    %(end_line)s, %(embedding)s
                )
                ON CONFLICT (chunk_id) DO UPDATE SET
                    request_id = EXCLUDED.request_id,
                    document_id = EXCLUDED.document_id,
                    source_type = EXCLUDED.source_type,
                    chunk_index = EXCLUDED.chunk_index,
                    content = EXCLUDED.content,
                    page_number = EXCLUDED.page_number,
                    start_line = EXCLUDED.start_line,
                    end_line = EXCLUDED.end_line,
                    embedding = EXCLUDED.embedding
                """,
                {
                    "chunk_id": chunk.chunk_id,
                    "request_id": request_id,
                    "document_id": chunk.document_id,
                    "source_type": chunk.source_type,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "embedding": Vector(vector),
                },
            )
        conn.commit()


def retrieve_vector_documents(
    query: str,
    request_id: str,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """request_id로 스코프를 좁혀 코사인 유사도 상위 top_k를 가져온다.

    Args:
        query: 검색 쿼리 문장. config.get_embeddings()로 벡터화한다.
        request_id: 반드시 이 값으로 필터링한다(다른 요청의 자료가 섞이면 안 됨).
        top_k: 없으면 config.VECTOR_TOP_K. config.SIMILARITY_THRESHOLD 미만인
            매치는 결과에서 제외한다.

    Returns:
        distance(코사인 거리)와 vector_rank(1부터)가 채워진 RetrievedChunk 리스트.
        조건에 맞는 결과가 없으면 빈 리스트.
    """
    top_k = top_k if top_k is not None else config.VECTOR_TOP_K
    embeddings = config.get_embeddings()
    query_vector = Vector(embeddings.embed_query(query))

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT chunk_id, document_id, source_type, content, chunk_index,
                   page_number, start_line, end_line,
                   (embedding <=> %(query_vector)s) AS distance
            FROM {TABLE_NAME}
            WHERE request_id = %(request_id)s
            ORDER BY embedding <=> %(query_vector)s
            LIMIT %(top_k)s
            """,
            {"query_vector": query_vector, "request_id": request_id, "top_k": top_k},
        )
        columns = [col.name for col in cur.description]
        rows = [dict(zip(columns, row, strict=True)) for row in cur.fetchall()]

    results: list[RetrievedChunk] = []
    for row in rows:
        similarity = 1 - row["distance"]
        if similarity < config.SIMILARITY_THRESHOLD:
            continue
        results.append(
            RetrievedChunk(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                source_type=row["source_type"],
                content=row["content"],
                chunk_index=row["chunk_index"],
                page_number=row["page_number"],
                start_line=row["start_line"],
                end_line=row["end_line"],
                distance=row["distance"],
                vector_rank=len(results) + 1,
                retrieval_sources=["vector"],
            )
        )
    return results
