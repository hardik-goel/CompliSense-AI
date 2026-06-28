"""Google Cloud Storage artefact collector (agent-side; bytes stay local).

Needs read access to the bucket/prefix (e.g. roles/storage.objectViewer scoped to the bucket).
Default auth uses Application Default Credentials.
"""

from __future__ import annotations

import posixpath
from typing import Any, List

from agent.collectors.base import Candidate
from agent.collectors.extract import SUPPORTED_EXTS, extract_text

DEFAULT_MAX_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_FILES = 200


def _ext_ok(name: str) -> bool:
    i = name.rfind(".")
    return i >= 0 and name[i:].lower() in SUPPORTED_EXTS


def collect_gcs_candidates(bucket: str, prefix: str = "", client: Any = None,
                           max_files: int = DEFAULT_MAX_FILES,
                           max_bytes: int = DEFAULT_MAX_BYTES) -> List[Candidate]:
    """List blobs under prefix and return candidates. `client` is an injectable storage.Client."""
    if not bucket:
        raise ValueError("bucket is required for the GCS collector")
    if client is None:
        from google.cloud import storage  # lazy
        client = storage.Client()

    out: List[Candidate] = []
    for blob in client.list_blobs(bucket, prefix=prefix):
        if len(out) >= max_files:
            break
        name = getattr(blob, "name", "")
        size = getattr(blob, "size", 0) or 0
        if name.endswith("/") or not _ext_ok(name) or size == 0 or size > max_bytes:
            continue
        body = blob.download_as_bytes()
        sample = extract_text(body, posixpath.basename(name))
        if not sample.strip():
            continue
        out.append(Candidate(source="gcs", ref=f"gs://{bucket}/{name}",
                             filename=posixpath.basename(name), sample=sample, data=body))
    return out
