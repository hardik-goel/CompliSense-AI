"""Crawl a local / on-prem folder for candidate artefact files (text-like, size-capped)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List

# Only text-like files we can sample/classify. (PDF/DOCX extraction is a later upgrade.)
TEXT_EXTS = {".md", ".markdown", ".txt", ".rst", ".json", ".yaml", ".yml", ".csv", ".html", ".htm", ".ini", ".cfg", ".toml"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "complisense_env", ".idea", "dist", "build"}
DEFAULT_MAX_BYTES = 2 * 1024 * 1024  # 2 MB
SAMPLE_BYTES = 4096


@dataclass
class Candidate:
    path: str       # absolute
    rel: str        # relative to source root
    filename: str
    size: int
    sample: str


def crawl(source_path: str, max_bytes: int = DEFAULT_MAX_BYTES) -> List[Candidate]:
    root = Path(source_path).resolve()
    if not root.exists() or not root.is_dir():
        raise NotADirectoryError(f"Source path is not a folder: {root}")
    out: List[Candidate] = []
    for c in _iter(root, max_bytes):
        out.append(c)
    return out


def _iter(root: Path, max_bytes: int) -> Iterator[Candidate]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() not in TEXT_EXTS:
                continue
            try:
                size = p.stat().st_size
            except OSError:
                continue
            if size == 0 or size > max_bytes:
                continue
            try:
                sample = p.read_text(encoding="utf-8", errors="ignore")[:SAMPLE_BYTES]
            except Exception:
                continue
            yield Candidate(path=str(p), rel=str(p.relative_to(root)), filename=fn, size=size, sample=sample)
