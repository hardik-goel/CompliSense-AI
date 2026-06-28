"""Artefact generator API (Tier-1.5)."""

import asyncio

import pytest

import saas.app.artefacts_api as A


def _run(coro):
    return asyncio.run(coro)


USER = {"id": "u1", "email": "owner@x.com"}
# privacy_notice (DPDP-SEC5-NOTICE-001) is a gap when has_privacy_notice is False.
PROJECT = {"id": "p1", "user_id": "u1",
           "discovered_manifest": {"has_privacy_notice": False, "has_security_safeguards": True}}


class _Col:
    def __init__(self): self.docs = []
    def find(self, q): return [d for d in self.docs if all(d.get(k) == v for k, v in q.items())]
    def find_one(self, q): return next((d for d in self.docs if all(d.get(k) == v for k, v in q.items())), None)
    def update_one(self, q, u, upsert=False):
        d = self.find_one(q)
        if d is None:
            d = dict(q); self.docs.append(d)
        d.update(u.get("$set", {}))


class _FakeCopilot:
    def draft(self, rule, facts, artifact_type):
        return {"mode": "draft", "grounded": True,
                "answer": f"DRAFT — REQUIRES LEGAL REVIEW\n\n{artifact_type} for {rule['rule_id']}",
                "disclaimer": "not legal advice", "model": "claude-opus-4-8"}


def _patch(monkeypatch, role="owner", copilot=None):
    col = _Col()
    monkeypatch.setattr(A, "artefacts_collection", lambda: col)
    monkeypatch.setattr(A, "get_project_with_role", lambda pid, user, action: (PROJECT, role))
    monkeypatch.setattr(A, "get_copilot", lambda: copilot or _FakeCopilot())
    monkeypatch.setattr(A, "insert_audit_log", lambda *a, **k: None)
    return col


def test_needed_lists_artefacts_and_sources(monkeypatch):
    _patch(monkeypatch)
    body = _run(A.list_needed("p1", current_user=USER))
    ids = {a["artefact_id"] for a in body["artefacts"]}
    assert "privacy_notice" in ids
    assert body["we_can_connect_to"] == ["AWS", "GCP", "Azure", "GitHub"]
    assert "sources_legend" in body


def test_draft_requires_consent(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=False, current_user=USER))
    assert e.value.status_code == 400


def test_draft_then_approve_then_export(monkeypatch):
    col = _patch(monkeypatch)
    d = _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=True, current_user=USER))
    assert d["status"] == "drafted" and "REQUIRES LEGAL REVIEW" in d["content"]
    assert col.find_one({"project_id": "p1", "art_id": "privacy_notice"})["status"] == "drafted"
    # cannot export before approval
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        _run(A.export_approved("p1", current_user=USER))
    assert e.value.status_code == 404
    # approve -> export works
    ap = _run(A.approve_artefact("p1", "privacy_notice", current_user=USER))
    assert ap["status"] == "approved"
    resp = _run(A.export_approved("p1", current_user=USER))
    assert resp.media_type == "application/zip" and "attachment" in resp.headers["content-disposition"]


def test_draft_unknown_artefact_404(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(A.draft_artefact("p1", "nope", consent_to_send=True, current_user=USER))
    assert e.value.status_code == 404


def test_draft_copilot_failure_502(monkeypatch):
    from fastapi import HTTPException
    class Boom:
        def draft(self, *a): raise RuntimeError("no api key")
    _patch(monkeypatch, copilot=Boom())
    with pytest.raises(HTTPException) as e:
        _run(A.draft_artefact("p1", "privacy_notice", consent_to_send=True, current_user=USER))
    assert e.value.status_code == 502


def test_approve_requires_a_draft(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(A.approve_artefact("p1", "privacy_notice", current_user=USER))
    assert e.value.status_code == 404  # nothing drafted yet
