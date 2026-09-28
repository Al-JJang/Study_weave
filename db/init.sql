-- 컨테이너 첫 생성 시 1회만 실행됨 (docker-entrypoint-initdb.d)
-- CI의 db-integration job은 매번 새 컨테이너에 이 파일을 직접 psql -f 로 실행한다.
-- store.vector_store.initialize_vector_db() 도 동일한 DDL을 Python에서 실행하므로
-- 두 정의가 어긋나지 않도록 컬럼을 바꿀 때는 반드시 함께 수정한다.

CREATE EXTENSION IF NOT EXISTS vector;

-- Chunk 규격(schemas/files.py의 Chunk)을 그대로 반영한 테이블.
-- embedding 차원(1536)은 config.EMBEDDING_DIMENSION(gemini-embedding-2 기준, WEAVE-19)과 맞춘다.
-- 임베딩 모델을 바꿔 차원이 달라지면 이 컬럼과 config.EMBEDDING_DIMENSION을 함께 바꾸고
-- 테이블을 재생성해야 한다(기존 벡터는 재사용 불가).
CREATE TABLE IF NOT EXISTS studywave_chunks (
    chunk_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('pdf', 'code')),
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    content TEXT NOT NULL,
    page_number INTEGER CHECK (page_number IS NULL OR page_number >= 1),
    start_line INTEGER CHECK (start_line IS NULL OR start_line >= 1),
    end_line INTEGER CHECK (end_line IS NULL OR end_line >= 1),
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- retrieve_vector_documents가 항상 request_id로 먼저 스코프를 좁히므로 필수 인덱스.
CREATE INDEX IF NOT EXISTS idx_studywave_chunks_request_id
    ON studywave_chunks (request_id);

-- 코사인 거리(<=>) 기준 근사 최근접 검색용. SIMILARITY_THRESHOLD(config.py)는
-- 1 - cosine distance 로 해석하므로 인덱스도 vector_cosine_ops로 맞춘다.
CREATE INDEX IF NOT EXISTS idx_studywave_chunks_embedding
    ON studywave_chunks USING hnsw (embedding vector_cosine_ops);
