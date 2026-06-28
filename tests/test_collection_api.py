"""Collection sources API (declare-sources, 6.5)."""

import asyncio

import pytest

import saas.app.collection_api as C


def _run(coro):
    return asyncio.run(coro)


USER = {"id": "u1", "email": "o@x.com"}


class _Projects:
    def __init__(self, project): self.project = project
    def update_one(self, q, u): self.project.update(u.get("$set", {}))


def _patch(monkeypatch, project):
    col = _Projects(project)
    monkeypatch.setattr(C, "_projects", lambda: col)
    monkeypatch.setattr(C, "get_project_with_role", lambda pid, user, action: (project, "owner"))
    monkeypatch.setattr(C, "insert_audit_log", lambda *a, **k: None)
    return col


def test_add_list_config_remove(monkeypatch):
    project = {"id": "p1"}
    _patch(monkeypatch, project)

    added = _run(C.add_source("p1", {"type": "s3", "config": {"bucket": "b", "prefix": "docs/"}}, current_user=USER))
    sid = added["source"]["id"]
    assert added["source"]["type"] == "s3" and sid

    listed = _run(C.list_sources("p1", current_user=USER))
    assert len(listed["sources"]) == 1

    cfg = _run(C.collection_config("p1", current_user=USER))
    assert cfg["sources"][0]["type"] == "s3" and "Credentials" in cfg["note"]

    removed = _run(C.remove_source("p1", sid, current_user=USER))
    assert removed["removed"] == sid
    assert _run(C.list_sources("p1", current_user=USER))["sources"] == []


def test_add_rejects_secret(monkeypatch):
    from fastapi import HTTPException
    project = {"id": "p1"}
    _patch(monkeypatch, project)
    with pytest.raises(HTTPException) as e:
        _run(C.add_source("p1", {"type": "github", "config": {"repo": "o/r", "token": "x"}}, current_user=USER))
    assert e.value.status_code == 400


def test_remove_missing_404(monkeypatch):
    from fastapi import HTTPException
    project = {"id": "p1", "collection_sources": []}
    _patch(monkeypatch, project)
    with pytest.raises(HTTPException) as e:
        _run(C.remove_source("p1", "nope", current_user=USER))
    assert e.value.status_code == 404
