"""Tests for src.parser."""

from __future__ import annotations

import io
from dataclasses import dataclass

import pytest

from src.parser import parse_uploaded_file


@dataclass
class FakeUpload:
    """Minimal stand-in for Streamlit's UploadedFile."""

    name: str
    payload: bytes

    def read(self) -> bytes:
        return self.payload


class TestParseUploadedFile:
    def test_parses_plain_txt(self):
        upload = FakeUpload("notes.txt", "hello world".encode("utf-8"))
        assert parse_uploaded_file(upload) == "hello world"

    def test_parses_markdown(self):
        upload = FakeUpload("spec.md", "# Title\nBody".encode("utf-8"))
        assert parse_uploaded_file(upload) == "# Title\nBody"

    def test_handles_non_utf8_gracefully(self):
        upload = FakeUpload("weird.txt", b"\xff\xfehello")
        out = parse_uploaded_file(upload)
        assert "hello" in out

    def test_parses_docx(self, tmp_path):
        docx = pytest.importorskip("docx")
        path = tmp_path / "req.docx"
        doc = docx.Document()
        doc.add_paragraph("First requirement.")
        doc.add_paragraph("")
        doc.add_paragraph("Second requirement.")
        doc.save(path)

        with open(path, "rb") as fh:
            wrapped = io.BytesIO(fh.read())
        wrapped.name = "req.docx"  # type: ignore[attr-defined]

        text = parse_uploaded_file(wrapped)
        assert "First requirement." in text
        assert "Second requirement." in text
        assert "\n\n" not in text  # empty paragraphs stripped
