"""Best-effort text extraction for candidate files (text, PDF, DOCX).

All heavy parsers are lazy-imported so the collector still runs when they aren't installed —
extraction just returns "" for that format and the file is skipped. Used by every source
collector to produce a content sample for classification. Runs locally; bytes never leave the
machine.
"""

from __future__ import annotations

import io

# Extensions we can pull text from. Plain-text first, then the rich formats.
TEXT_EXTS = {".md", ".markdown", ".txt", ".rst", ".json", ".yaml", ".yml", ".csv",
             ".html", ".htm", ".ini", ".cfg", ".toml"}
RICH_EXTS = {".pdf", ".docx"}
SUPPORTED_EXTS = TEXT_EXTS | RICH_EXTS


def _ext(filename: str) -> str:
    i = filename.rfind(".")
    return filename[i:].lower() if i >= 0 else ""


def extract_text(data: bytes, filename: str, max_chars: int = 8000) -> str:
    """Extract a text sample from raw bytes based on the filename's extension. Never raises."""
    ext = _ext(filename)
    try:
        if ext == ".pdf":
            return _pdf(data)[:max_chars]
        if ext == ".docx":
            return _docx(data)[:max_chars]
        if ext in TEXT_EXTS:
            return data.decode("utf-8", errors="ignore")[:max_chars]
    except Exception:
        return ""
    return ""


def _pdf(data: bytes) -> str:
    try:
        import pypdf  # lazy
    except Exception:
        return ""
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        out = []
        for page in reader.pages[:20]:  # cap pages
            out.append(page.extract_text() or "")
        return "\n".join(out)
    except Exception:
        return ""


def _docx(data: bytes) -> str:
    try:
        import docx  # python-docx, lazy
    except Exception:
        return ""
    try:
        d = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs)
    except Exception:
        return ""
