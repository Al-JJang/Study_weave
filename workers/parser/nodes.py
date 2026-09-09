"""
B — Graph Node.

parse_files_node  → parsed_chunks, files
retrieve_chunks_node → retrieved_chunks  (store/vector_store.py)

연동:
    pdf_parser.py, code_parser.py, preprocess.py
    store/vector_store.py
    graph/supervisor.py
"""

from __future__ import annotations

from schemas.files import Chunk, FileInfo, RetrievedChunk
from schemas.state import AgentState


def make_document_id(request_id: str, filename: str) -> str:
    return f"{request_id}:{filename.replace(' ', '_')}"


def make_chunk_id(document_id: str, chunk_index: int) -> str:
    return f"{document_id}:chunk:{chunk_index:04d}"


def parse_files_node(state: AgentState) -> dict:
    raise NotImplementedError("B: parse_files_node")


def retrieve_chunks_node(state: AgentState) -> dict:
    raise NotImplementedError("B: retrieve_chunks_node")
