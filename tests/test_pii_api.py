"""PII / data-flow inference API (Phase 4.3)."""

import asyncio

import pytest

import saas.app.pii_api as P


def _run(coro):
    return asyncio.run(coro)


class _Col:
    def __init__(self): self.docs = []
    def insert_one(self, d): self.docs.append(d)
    def find(self, q):
        class C(list):
            def sort(self, *a, **k): return self
        return C([d for d in self.docs if all(d.get(k) == v for k, v in q.items())])
    def find_one(self, q): return next((d for d in self.docs if all(d.get(k) == v for k, v in q.items())), None)
    def update_one(self, q, u):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                d.update(u.get("$set", {})); return


USER = {"id": "u1"}


def _patch(monkeypatch):
    pii, projects = _Col(), _Col()
    projects.insert_one({"id": "p1", "user_id": "u1", "name": "P1"})
    monkeypatch.setattr(P, "pii_collection", lambda: pii)
    monkeypatch.setattr(P, "projects_collection", lambda: projects)
    monkeypatch.setattr(P, "get_project_for_user", lambda pid, uid: {"id": pid, "user_id": uid})
    monkeypatch.setattr(P, "insert_audit_log", lambda *a, **k: None)
    return pii, projects


def _src(name, fields, provider=None, region=None):
    return P.PIISourceIn(name=name, field_names=fields, provider=provider, region=region)


def test_infer_returns_report_no_store(monkeypatch):
    pii, _ = _patch(monkeypatch)
    body = _run(P.infer("p1", P.InferRequest(
        sources=[_src("db", ["user_email", "pan"], "aws", "ap-south-1")]), current_user=USER))
    assert body["stored"] is False and body["inference_id"] is None
    fields = {s["manifest_field"] for s in body["report"]["suggestions"]}
    assert "pii_categories" in fields
    assert pii.docs == []


def test_infer_field_names_shorthand(monkeypatch):
    _patch(monkeypatch)
    body = _run(P.infer("p1", P.InferRequest(field_names=["aadhaar", "mobile"]), current_user=USER))
    cats = next(s for s in body["report"]["suggestions"] if s["manifest_field"] == "pii_categories")["suggested_value"]
    assert set(cats) >= {"government_id", "phone"}


def test_infer_requires_input(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(P.infer("p1", P.InferRequest(), current_user=USER))
    assert e.value.status_code == 400


def test_infer_persists_with_consent(monkeypatch):
    pii, _ = _patch(monkeypatch)
    body = _run(P.infer("p1", P.InferRequest(
        sources=[_src("db", ["email"], "aws", "ap-south-1")], consent_to_store=True), current_user=USER))
    assert body["stored"] is True and len(pii.docs) == 1


def test_apply_merges_into_discovered_manifest(monkeypatch):
    pii, projects = _patch(monkeypatch)
    body = _run(P.infer("p1", P.InferRequest(
        sources=[_src("db", ["user_email", "pan"], "aws", "ap-south-1")], consent_to_store=True), current_user=USER))
    applied = _run(P.apply("p1", body["inference_id"],
                   P.ApplyRequest(accepted_fields=["pii_categories", "storage_locations"]), current_user=USER))
    dm = applied["discovered_manifest"]
    assert set(dm["pii_categories"]) >= {"email", "government_id"}
    assert dm["storage_locations"] == ["aws"]
    # persisted on project + recorded on inference
    assert projects.find_one({"id": "p1"})["discovered_manifest"]["pii_categories"]
    assert "pii_categories" in pii.docs[0]["applied_fields"]


def test_apply_unions_with_existing_manifest(monkeypatch):
    pii, projects = _patch(monkeypatch)
    projects.find_one({"id": "p1"})["discovered_manifest"] = {"storage_locations": ["gcp"]}
    body = _run(P.infer("p1", P.InferRequest(
        sources=[_src("db", ["email"], "aws", "ap-south-1")], consent_to_store=True), current_user=USER))
    applied = _run(P.apply("p1", body["inference_id"],
                   P.ApplyRequest(accepted_fields=["storage_locations"]), current_user=USER))
    assert applied["discovered_manifest"]["storage_locations"] == ["aws", "gcp"]  # union


def test_apply_unknown_inference_404(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(P.apply("p1", "nope", P.ApplyRequest(accepted_fields=["pii_categories"]), current_user=USER))
    assert e.value.status_code == 404


def test_list_and_get(monkeypatch):
    _patch(monkeypatch)
    body = _run(P.infer("p1", P.InferRequest(
        sources=[_src("db", ["email"], "gcp", "us-east1")], consent_to_store=True), current_user=USER))
    listed = _run(P.list_inferences("p1", current_user=USER))
    assert listed["count"] == 1 and listed["inferences"][0]["has_cross_border"] is True
    detail = _run(P.get_inference("p1", body["inference_id"], current_user=USER))
    assert "report" in detail
