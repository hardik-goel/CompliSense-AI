"""GitHub repo-file artefact collector (agent-side; bytes stay local).

Reads files from a repo (optionally under a path) via the GitHub REST API. A token is optional
for public repos, required for private ones (scope: repo:read / contents:read). The HTTP client
is injectable for tests.
"""

from __future__ import annotations

import posixpath
from typing import Any, List, Optional

from agent.collectors.base import Candidate
from agent.collectors.extract import SUPPORTED_EXTS, extract_text

DEFAULT_MAX_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_FILES = 200


def _ext_ok(path: str) -> bool:
    i = path.rfind(".")
    return i >= 0 and path[i:].lower() in SUPPORTED_EXTS


class _RealGitHub:
    """Lists files via the git-tree API and fetches raw bytes. Lazy `requests`."""

    def __init__(self, repo: str, ref: Optional[str], token: Optional[str]):
        self.repo = repo
        self.ref = ref or "HEAD"
        self._headers = {"Accept": "application/vnd.github+json"}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def list_files(self, path: str) -> List[str]:
        import requests  # lazy
        url = f"https://api.github.com/repos/{self.repo}/git/trees/{self.ref}?recursive=1"
        data = requests.get(url, headers=self._headers, timeout=30).json()
        prefix = path.strip("/")
        return [t["path"] for t in data.get("tree", [])
                if t.get("type") == "blob" and (not prefix or t["path"].startswith(prefix + "/") or t["path"] == prefix)]

    def get_file(self, path: str) -> bytes:
        import requests  # lazy
        url = f"https://raw.githubusercontent.com/{self.repo}/{self.ref}/{path}"
        return requests.get(url, headers=self._headers, timeout=30).content


def collect_github_candidates(repo: str, path: str = "", ref: Optional[str] = None,
                              token: Optional[str] = None, gh: Any = None,
                              max_files: int = DEFAULT_MAX_FILES,
                              max_bytes: int = DEFAULT_MAX_BYTES) -> List[Candidate]:
    """Read repo files under `path`, return candidates. `gh` is an injectable client."""
    if not repo or "/" not in repo:
        raise ValueError("repo must be 'owner/name'")
    gh = gh or _RealGitHub(repo, ref, token)

    out: List[Candidate] = []
    for fpath in gh.list_files(path):
        if len(out) >= max_files:
            break
        if not _ext_ok(fpath):
            continue
        body = gh.get_file(fpath)
        if not body or len(body) > max_bytes:
            continue
        sample = extract_text(body, posixpath.basename(fpath))
        if not sample.strip():
            continue
        out.append(Candidate(source="github", ref=f"github://{repo}/{fpath}",
                             filename=posixpath.basename(fpath), sample=sample, data=body))
    return out
