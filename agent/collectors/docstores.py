"""Document-store collectors: Notion, Google Drive, SharePoint (agent-side; bytes stay local).

These are OAuth/token sources. Obtaining the access token (registering an OAuth app / Notion
integration) is deployment setup the customer does once; this module takes a token and reads.
Each real client exposes the same tiny interface — list_documents() + get_document(id) — and a
generic collector turns the results into candidates. Clients are injectable for tests.

Token acquisition (out of scope of this code, done once by the customer):
- Notion       : create an internal integration -> "Internal Integration Token"; share the
                 database/pages with it.
- Google Drive : OAuth client (scope drive.readonly) -> access token.
- SharePoint   : Entra app (scope Sites.Read.All / Files.Read.All) -> Graph access token.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from agent.collectors.base import Candidate
from agent.collectors.extract import extract_text

DEFAULT_MAX_FILES = 200
DEFAULT_MAX_BYTES = 8 * 1024 * 1024
NOTION_VERSION = "2022-06-28"


def _collect_docstore(source: str, client: Any, max_files: int = DEFAULT_MAX_FILES,
                      max_bytes: int = DEFAULT_MAX_BYTES) -> List[Candidate]:
    out: List[Candidate] = []
    for doc in client.list_documents():
        if len(out) >= max_files:
            break
        filename, data = client.get_document(doc["id"])
        if not data or len(data) > max_bytes:
            continue
        sample = extract_text(data, filename)
        if not sample.strip():
            continue
        out.append(Candidate(source=source, ref=f"{source}://{doc.get('name', doc['id'])}",
                             filename=filename, sample=sample, data=data))
    return out


# ---------------- Notion ----------------
class NotionClient:
    def __init__(self, token: str, database_id: Optional[str] = None):
        self.token = token
        self.database_id = database_id
        self._h = {"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION,
                   "Content-Type": "application/json"}

    def list_documents(self) -> List[dict]:
        import requests  # lazy
        if self.database_id:
            r = requests.post(f"https://api.notion.com/v1/databases/{self.database_id}/query",
                              headers=self._h, json={}, timeout=30).json()
        else:
            r = requests.post("https://api.notion.com/v1/search", headers=self._h,
                              json={"filter": {"property": "object", "value": "page"}}, timeout=30).json()
        return [{"id": p["id"], "name": _notion_title(p)} for p in r.get("results", [])]

    def get_document(self, page_id: str) -> Tuple[str, bytes]:
        import requests  # lazy
        r = requests.get(f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100",
                         headers=self._h, timeout=30).json()
        text = "\n".join(_notion_block_text(b) for b in r.get("results", []))
        return f"{page_id}.md", text.encode("utf-8")


def _notion_title(page: dict) -> str:
    for prop in (page.get("properties") or {}).values():
        if prop.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in prop.get("title", [])) or page["id"]
    return page["id"]


def _notion_block_text(block: dict) -> str:
    t = block.get("type", "")
    rich = (block.get(t) or {}).get("rich_text", []) if isinstance(block.get(t), dict) else []
    return "".join(r.get("plain_text", "") for r in rich)


def collect_notion_candidates(token: str, database_id: Optional[str] = None,
                              client: Any = None, **kw) -> List[Candidate]:
    return _collect_docstore("notion", client or NotionClient(token, database_id), **kw)


# ---------------- Google Drive ----------------
class GDriveClient:
    def __init__(self, token: str, folder_id: Optional[str] = None):
        self.token = token
        self.folder_id = folder_id
        self._h = {"Authorization": f"Bearer {token}"}

    def list_documents(self) -> List[dict]:
        import requests  # lazy
        q = f"'{self.folder_id}' in parents" if self.folder_id else "trashed=false"
        r = requests.get("https://www.googleapis.com/drive/v3/files",
                         headers=self._h, params={"q": q, "fields": "files(id,name,mimeType)"},
                         timeout=30).json()
        return [{"id": f["id"], "name": f["name"], "mimeType": f.get("mimeType", "")}
                for f in r.get("files", [])]

    def get_document(self, file_id: str) -> Tuple[str, bytes]:
        import requests  # lazy
        meta = requests.get(f"https://www.googleapis.com/drive/v3/files/{file_id}",
                            headers=self._h, params={"fields": "name,mimeType"}, timeout=30).json()
        name, mime = meta.get("name", file_id), meta.get("mimeType", "")
        if mime.startswith("application/vnd.google-apps"):
            content = requests.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}/export",
                headers=self._h, params={"mimeType": "text/plain"}, timeout=30).content
            return f"{name}.txt", content
        content = requests.get(f"https://www.googleapis.com/drive/v3/files/{file_id}",
                               headers=self._h, params={"alt": "media"}, timeout=30).content
        return name, content


def collect_gdrive_candidates(token: str, folder_id: Optional[str] = None,
                              client: Any = None, **kw) -> List[Candidate]:
    return _collect_docstore("gdrive", client or GDriveClient(token, folder_id), **kw)


# ---------------- SharePoint / OneDrive (Microsoft Graph) ----------------
class SharePointClient:
    def __init__(self, token: str, site: Optional[str] = None):
        self.token = token
        self.site = site
        self._h = {"Authorization": f"Bearer {token}"}

    def _base(self) -> str:
        return f"https://graph.microsoft.com/v1.0/sites/{self.site}/drive" if self.site \
            else "https://graph.microsoft.com/v1.0/me/drive"

    def list_documents(self) -> List[dict]:
        import requests  # lazy
        r = requests.get(f"{self._base()}/root/children", headers=self._h, timeout=30).json()
        return [{"id": it["id"], "name": it.get("name", it["id"])}
                for it in r.get("value", []) if "file" in it]

    def get_document(self, item_id: str) -> Tuple[str, bytes]:
        import requests  # lazy
        meta = requests.get(f"{self._base()}/items/{item_id}", headers=self._h, timeout=30).json()
        content = requests.get(f"{self._base()}/items/{item_id}/content",
                               headers=self._h, timeout=30).content
        return meta.get("name", item_id), content


def collect_sharepoint_candidates(token: str, site: Optional[str] = None,
                                  client: Any = None, **kw) -> List[Candidate]:
    return _collect_docstore("sharepoint", client or SharePointClient(token, site), **kw)


def collect_docstore_candidates(kind: str, args) -> List[Candidate]:
    """CLI dispatch for the doc-store sources."""
    if kind == "notion":
        return collect_notion_candidates(args.token, database_id=args.database_id)
    if kind == "gdrive":
        return collect_gdrive_candidates(args.token, folder_id=args.path or None)
    if kind == "sharepoint":
        return collect_sharepoint_candidates(args.token, site=args.site)
    raise ValueError(f"unknown doc store: {kind}")
