"""
공통 환경 설정.

강의 매핑:
    day1/hybridRagEx1.py  §1 환경 설정 및 경로
        google.genai.Client, GENERATION_MODEL, EMBEDDING_MODEL, EMBEDDING_DIMESION
    day2/hybridRagEx5.py  §1~4 환경변수 / Gemini / 검색 설정
    day2/agentEx2.py ~ day3/agentEx5.py
        ChatGoogleGenerativeAI(model=, api_key=, temperature=0)
        os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
    day3/agentEx5.py
        GoogleGenerativeAIEmbeddings(model=, output_dimensionality=768)
        load_dotenv, BASE_DIR, DATA_DIR, CHROMA_DIR, COLLECTION_NAME

프로바이더 정책 (스터디 기본안):
    - 생성(C) / 임베딩(B) 기본값 = Gemini (교육장 Tier 3 키)
    - 검증(D) / 라우팅(A) 은 규칙 기반으로도 가능. 쿼터 아끼려면 OSS(Ollama)
    - 합의 벡터 DB = PostgreSQL + pgvector (store/vector_store.py)
    - 강의 실습은 Chroma. VECTOR_BACKEND=chroma 로 바꾸면 같은 함수 시그니처로 연습 가능
    - 임베딩 모델을 바꾸면 collection/테이블을 새로 만들어야 한다 (차원 불일치)

스터디에서 할 일:
    - 프로젝트 루트에 .env 만들고 GEMINI_API_KEY 넣기 (키 값을 코드에 하드코딩 금지)
    - LLM_PROVIDER / EMBEDDING_PROVIDER 를 gemini | ollama 로 전환 실험
    - EMBEDDING_DIMENSION 과 Chroma 차원을 맞출지 팀 합의
    - TOP_K / DISTANCE_THRESHOLD 초기값 확정 (체크리스트 Tier 2)
    - get_chat_model() / get_embeddings() 를 직접 구현 (아래는 슬롯만)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "studywave_chroma_db"
COLLECTION_NAME = "studywave_chunks"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost:5432/studywave",
)
VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "pgvector")  # pgvector | chroma

DATA_DIR.mkdir(parents=True, exist_ok=True)

ProviderName = Literal["gemini", "ollama"]

# ---------------------------------------------------------------------------
# Dual provider — Gemini(기본) / Ollama(선택)
# .env 예:
#   GEMINI_API_KEY=교육장에서_받은_키
#   GEMINI_MODEL=gemini-3.7-flash
#   GEMINI_EMBEDDING_MODEL=gemini-embedding-2
#   LLM_PROVIDER=gemini
#   EMBEDDING_PROVIDER=gemini
#   # OSS 로 바꿀 때만:
#   LLM_PROVIDER=ollama
#   EMBEDDING_PROVIDER=ollama
#   OLLAMA_BASE_URL=http://localhost:11434
#   OLLAMA_CHAT_MODEL=gemma3:4b
#   OLLAMA_EMBED_MODEL=nomic-embed-text
#   OLLAMA_VERIFY_MODEL=llama3.2:3b
# ---------------------------------------------------------------------------

def _as_provider(name: str, default: str) -> ProviderName:
    value = os.getenv(name, default).strip().lower()
    if value not in ("gemini", "ollama"):
        raise ValueError(f"{name} 는 gemini 또는 ollama 여야 합니다. 현재: {value!r}")
    return value  # type: ignore[return-value]


LLM_PROVIDER = _as_provider("LLM_PROVIDER", "gemini")
EMBEDDING_PROVIDER = _as_provider("EMBEDDING_PROVIDER", "gemini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")

# day1 GENERATION_MODEL / EMBEDDING_MODEL 별칭
GENERATION_MODEL = GEMINI_MODEL
EMBEDDING_MODEL = GEMINI_EMBEDDING_MODEL
# 강의 코드의 EMBEDDING_DIMESION(오타) 과 같은 값. 철자만 바로잡음.
# nomic-embed-text 도 768. bge-m3 로 바꾸면 1024 로 맞추고 collection 재생성.
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))

# OpenAI-compatible 엔드포인트도 가능 (Ollama: http://localhost:11434/v1)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "gemma3:4b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
# A 검증 전용. 생성보다 작고 JSON 잘 지키는 쪽을 권장.
OLLAMA_VERIFY_MODEL = os.getenv("OLLAMA_VERIFY_MODEL", "llama3.2:3b")
# A 라우팅을 LLM 으로 바꿀 때. 기본 파이프라인은 규칙 기반 detect_route.
OLLAMA_ROUTE_MODEL = os.getenv("OLLAMA_ROUTE_MODEL", "llama3.2:1b")

VECTOR_TOP_K = 5
DISTANCE_THRESHOLD = None  # None 이면 threshold 없이 TOP_K 만 사용

# 입력 없는 마크다운 섹션: "omit" 이면 생략, "placeholder" 면 안내 문구
EMPTY_SECTION_POLICY = "omit"

# Node 실패 시: "partial" | "abort" | "retry"
NODE_FAILURE_POLICY = "partial"
MAX_RETRY_COUNT = 2


def require_gemini_key() -> str:
    """강의는 import 시점에 raise. 여기선 Mock Graph 가 키 없이 돌 수 있게 호출할 때만 검사."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY 가 없습니다. "
            "프로젝트 루트 .env 에 GEMINI_API_KEY=... 를 넣으세요."
        )
    return GEMINI_API_KEY


def get_chat_model(*, role: Literal["generate", "verify", "route"] = "generate"):
    """
    강의 ChatGoogleGenerativeAI / (선택) Ollama 분기.

    role:
        generate → C 노트·퀴즈 (기본 Gemini gemini-3.7-flash)
        verify   → A 검증 (쿼터 절약 시 ollama llama3.2:3b)
        route    → A 분류 (기본은 규칙. LLM 쓸 때만)

    스터디에서 채울 import:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_ollama import ChatOllama
        # 또는 OpenAI-compatible:
        # from langchain_openai import ChatOpenAI
        # ChatOpenAI(base_url=f"{OLLAMA_BASE_URL}/v1", api_key="ollama", model=...)
    """
    raise NotImplementedError(
        f"config.get_chat_model(role={role!r}) — "
        f"LLM_PROVIDER={LLM_PROVIDER}, EMBEDDING_PROVIDER={EMBEDDING_PROVIDER}"
    )


def get_embeddings():
    """
    강의 day3 GoogleGenerativeAIEmbeddings 또는 OllamaEmbeddings.

    스터디에서 채울 import:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_ollama import OllamaEmbeddings
        # day1 직접 SDK: from google import genai; from google.genai import types
        # client.models.embed_content(model=EMBEDDING_MODEL, ...,
        #     config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSION))
    """
    raise NotImplementedError(
        f"config.get_embeddings — EMBEDDING_PROVIDER={EMBEDDING_PROVIDER}"
    )
