"""Azure Blob Storage artefact collector (agent-side; bytes stay local).

Needs read access to the container/prefix (e.g. Storage Blob Data Reader). Default auth uses
azure.identity.DefaultAzureCredential against https://<account>.blob.core.windows.net.
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


def collect_azure_candidates(account_url: str, container: str, prefix: str = "",
                             container_client: Any = None, max_files: int = DEFAULT_MAX_FILES,
                             max_bytes: int = DEFAULT_MAX_BYTES) -> List[Candidate]:
    """List blobs under prefix and return candidates. `container_client` is injectable."""
    if not container:
        raise ValueError("container is required for the Azure Blob collector")
    if container_client is None:
        from azure.identity import DefaultAzureCredential  # lazy
        from azure.storage.blob import ContainerClient
        container_client = ContainerClient(account_url=account_url, container_name=container,
                                           credential=DefaultAzureCredential())

    out: List[Candidate] = []
    for blob in container_client.list_blobs(name_starts_with=prefix):
        if len(out) >= max_files:
            break
        name = getattr(blob, "name", "") if not isinstance(blob, dict) else blob.get("name", "")
        size = (getattr(blob, "size", 0) if not isinstance(blob, dict) else blob.get("size", 0)) or 0
        if name.endswith("/") or not _ext_ok(name) or size == 0 or size > max_bytes:
            continue
        body = container_client.download_blob(name).readall()
        sample = extract_text(body, posixpath.basename(name))
        if not sample.strip():
            continue
        out.append(Candidate(source="azure_blob", ref=f"azure://{container}/{name}",
                             filename=posixpath.basename(name), sample=sample, data=body))
    return out
