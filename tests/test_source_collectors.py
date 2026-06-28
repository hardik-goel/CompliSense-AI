"""Cloud / repo / doc-store collectors (injected fake clients — no creds, no network)."""

import io

import pytest

from agent.collectors.azure_blob import collect_azure_candidates
from agent.collectors.base import stage_candidates
from agent.collectors.docstores import (collect_gdrive_candidates, collect_notion_candidates,
                                        collect_sharepoint_candidates)
from agent.collectors.gcs import collect_gcs_candidates
from agent.collectors.github import collect_github_candidates
from agent.collectors.s3 import collect_s3_candidates

PRIVACY = b"personal data privacy policy purpose of processing"


# ---------------- S3 ----------------
class _Body:
    def __init__(self, b): self.b = b
    def read(self): return self.b


class _Paginator:
    def __init__(self, pages): self.pages = pages
    def paginate(self, **kw): return self.pages


class _FakeS3:
    def __init__(self, contents, objs): self._pages = [{"Contents": contents}]; self._objs = objs
    def get_paginator(self, name): return _Paginator(self._pages)
    def get_object(self, Bucket, Key): return {"Body": _Body(self._objs[Key])}


def test_s3_collects_supported_skips_others():
    contents = [{"Key": "docs/privacy_notice.md", "Size": len(PRIVACY)},
                {"Key": "docs/logo.png", "Size": 10},
                {"Key": "docs/huge.md", "Size": 99 * 1024 * 1024},
                {"Key": "docs/", "Size": 0}]
    s3 = _FakeS3(contents, {"docs/privacy_notice.md": PRIVACY})
    cands = collect_s3_candidates("bkt", prefix="docs/", client=s3)
    assert len(cands) == 1 and cands[0].source == "s3" and cands[0].filename == "privacy_notice.md"
    assert cands[0].ref == "s3://bkt/docs/privacy_notice.md"


def test_s3_requires_bucket():
    with pytest.raises(ValueError):
        collect_s3_candidates("", client=_FakeS3([], {}))


# ---------------- GCS ----------------
class _Blob:
    def __init__(self, name, data): self.name = name; self.size = len(data); self._d = data
    def download_as_bytes(self): return self._d


class _FakeGCS:
    def __init__(self, blobs): self.blobs = blobs
    def list_blobs(self, bucket, prefix=""): return [b for b in self.blobs if b.name.startswith(prefix)]


def test_gcs_collects():
    gcs = _FakeGCS([_Blob("d/retention_schedule.md", b"retention period erasure"),
                    _Blob("d/pic.png", b"x")])
    cands = collect_gcs_candidates("bkt", prefix="d/", client=gcs)
    assert len(cands) == 1 and cands[0].source == "gcs" and cands[0].ref == "gs://bkt/d/retention_schedule.md"


# ---------------- Azure Blob ----------------
class _AzItem:
    def __init__(self, name, size): self.name = name; self.size = size


class _AzDownload:
    def __init__(self, data): self._d = data
    def readall(self): return self._d


class _FakeContainer:
    def __init__(self, items, data): self._items = items; self._data = data
    def list_blobs(self, name_starts_with=""): return [b for b in self._items if b.name.startswith(name_starts_with)]
    def download_blob(self, name): return _AzDownload(self._data[name])


def test_azure_collects():
    items = [_AzItem("c/security_policy.md", 30), _AzItem("c/img.png", 5)]
    cc = _FakeContainer(items, {"c/security_policy.md": b"encryption access control least privilege"})
    cands = collect_azure_candidates("https://acct.blob.core.windows.net", "cont", prefix="c/", container_client=cc)
    assert len(cands) == 1 and cands[0].source == "azure_blob"


# ---------------- GitHub ----------------
class _FakeGH:
    def __init__(self, files): self.files = files
    def list_files(self, path): return [p for p in self.files if p.startswith(path)]
    def get_file(self, path): return self.files[path]


def test_github_collects_under_path():
    gh = _FakeGH({"docs/privacy_notice.md": PRIVACY, "src/main.py": b"print(1)", "docs/logo.png": b"x"})
    cands = collect_github_candidates("org/repo", path="docs", gh=gh)
    names = {c.filename for c in cands}
    assert names == {"privacy_notice.md"} and cands[0].ref == "github://org/repo/docs/privacy_notice.md"


def test_github_requires_owner_name():
    with pytest.raises(ValueError):
        collect_github_candidates("justname", gh=_FakeGH({}))


# ---------------- Doc stores ----------------
class _FakeDocClient:
    def __init__(self, docs): self.docs = docs  # [{id,name,filename,data}]
    def list_documents(self): return [{"id": d["id"], "name": d["name"]} for d in self.docs]
    def get_document(self, doc_id):
        d = next(x for x in self.docs if x["id"] == doc_id)
        return d["filename"], d["data"]


def test_notion_collects():
    c = _FakeDocClient([{"id": "p1", "name": "Privacy", "filename": "p1.md", "data": PRIVACY}])
    cands = collect_notion_candidates("tok", client=c)
    assert len(cands) == 1 and cands[0].source == "notion"


def test_gdrive_and_sharepoint_collect():
    c1 = _FakeDocClient([{"id": "f1", "name": "ret", "filename": "retention.txt", "data": b"retention erasure schedule"}])
    c2 = _FakeDocClient([{"id": "s1", "name": "sec", "filename": "security.md", "data": b"encryption access control"}])
    assert collect_gdrive_candidates("tok", client=c1)[0].source == "gdrive"
    assert collect_sharepoint_candidates("tok", client=c2)[0].source == "sharepoint"


# ---------------- end-to-end stage from a cloud source ----------------
def test_cloud_candidates_stage_and_classify(tmp_path):
    s3 = _FakeS3([{"Key": "x/privacy_notice.md", "Size": len(PRIVACY)}], {"x/privacy_notice.md": PRIVACY})
    cands = collect_s3_candidates("bkt", prefix="x/", client=s3)
    m = stage_candidates(cands, str(tmp_path / "out"), llm=None, source_label="s3")
    assert m["collected"] == 1 and m["matched"][0]["artefact_id"] == "privacy_notice"
    assert (tmp_path / "out" / "privacy_notice.md").read_bytes() == PRIVACY
