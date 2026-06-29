"""Parse user-uploaded files into plain text the LLM can ingest."""

from __future__ import annotations

from typing import BinaryIO, Protocol


class UploadedFileLike(Protocol):
    """Subset of Streamlit's UploadedFile we depend on."""

    name: str

    def read(self) -> bytes: ...


def parse_uploaded_file(uploaded: UploadedFileLike | BinaryIO) -> str:
    """Return the text content of an uploaded file.

    Supported: .txt, .md, .docx (others fall back to utf-8 decode).
    Empty paragraphs are stripped from .docx output for cleaner LLM input.
    """
    name = getattr(uploaded, "name", "").lower()

    if name.endswith(".docx"):
        # Import lazily so non-docx code paths don't need python-docx loaded.
        from docx import Document

        doc = Document(uploaded)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    raw = uploaded.read()
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="ignore")
    return str(raw)
