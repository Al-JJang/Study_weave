"""WEAVE-15: PDF 페이지 번호·목차 추출."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import Fit
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from schemas.files import FileInfo
from workers.parser.pdf_parser import parse_pdf


def _write_two_page_pdf(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawString(72, 720, "LangGraph StateGraph 개요")
    c.showPage()
    c.drawString(72, 720, "Chroma 검색과 request_id 필터")
    c.save()


def _write_pdf_with_toc(path: Path) -> None:
    _write_two_page_pdf(path)
    writer = PdfWriter(clone_from=str(path))
    writer.add_outline_item("개요", page_number=0, fit=Fit.fit())
    writer.add_outline_item("검색", page_number=1, fit=Fit.fit())
    with path.open("wb") as handle:
        writer.write(handle)


def test_parse_pdf_fills_page_numbers(tmp_path: Path) -> None:
    pdf_path = tmp_path / "lecture.pdf"
    _write_two_page_pdf(pdf_path)
    file = FileInfo(
        document_id="req-demo-001:lecture.pdf",
        filename="lecture.pdf",
        source_type="pdf",
        path=str(pdf_path),
    )

    chunks = parse_pdf(file)

    page_chunks = [chunk for chunk in chunks if not chunk.content.startswith("[목차]")]
    assert [chunk.page_number for chunk in page_chunks] == [1, 2]
    assert page_chunks[0].source_type == "pdf"
    assert "StateGraph" in page_chunks[0].content
    assert "request_id" in page_chunks[1].content
    assert page_chunks[0].chunk_id == "req-demo-001:lecture.pdf:chunk:0000"


def test_parse_pdf_extracts_toc(tmp_path: Path) -> None:
    pdf_path = tmp_path / "outlined.pdf"
    _write_pdf_with_toc(pdf_path)
    file = FileInfo(
        document_id="req-demo-001:outlined.pdf",
        filename="outlined.pdf",
        source_type="pdf",
        path=str(pdf_path),
    )

    chunks = parse_pdf(file)

    assert chunks[0].content.startswith("[목차]")
    assert "개요 (p.1)" in chunks[0].content
    assert "검색 (p.2)" in chunks[0].content
    assert chunks[0].page_number == 1
    assert [chunk.page_number for chunk in chunks[1:]] == [1, 2]
