"""Crawl a local / on-prem folder for candidate artefact files (text/PDF/DOCX, size-capped)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, List

from agent.collectors.base import Candidate
from agent.collectors.extract import SUPPORTED_EXTS, extract_text

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "complisense_env", ".idea", "dist", "build"}
DEFAULT_MAX_BYTES = 8 * 1024 * 1024  # 8 MB (PDFs are bigger than text)


def crawl(source_path: str, max_bytes: int = DEFAULT_MAX_BYTES) -> List[Candidate]:
    root = Path(source_path).resolve()
    if not root.exists() or not root.is_dir():
        raise NotADirectoryError(f"Source path is not a folder: {root}")
    return list(_iter(root, max_bytes))


def _iter(root: Path, max_bytes: int) -> Iterator[Candidate]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() not in SUPPORTED_EXTS:
                continue
            try:
                size = p.stat().st_size
            except OSError:
                continue
            if size == 0 or size > max_bytes:
                continue
            try:
                data = p.read_bytes()
            except Exception:
                continue
            sample = extract_text(data, fn)
            if not sample.strip():
                continue  # nothing readable (e.g. scanned PDF with no text layer, or parser missing)
            yield Candidate(source="local", ref=str(p.relative_to(root)), filename=fn,
                            sample=sample, data=data)
