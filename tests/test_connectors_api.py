"""Connector discovery API (Phase 3.2).

Handlers exercised directly (no TestClient), with fake collections + a fake connector
injected via get_connector, so no SDK/network is touched.
"""

import asyncio

import pytest

import saas.app.connectors_api as C
from connectors.base import ConnectorError, DiscoveredSignal


def _run(coro):
    return asyncio.run(coro)


class _Cursor:
    def __init__(self, docs): self._docs = list(docs)
    def sort(self, f, d): self._docs.sort(key=lambda x: x.get(f), reverse=d < 0); return self
    def __iter__(self): return iter(self._docs)


class _Col:
    def __init__(self): self.docs = []
    def insert_one(self, d): self.docs.append(d)
    def find(self, q): return _Cursor([d for d in self.docs if all(d.get(k) == v for k, v in q.items())])
    def find_one(self, q): return next((d for d in self.docs if all(d.get(k) == v for k, v in q.items())), None)
    def update_one(self, q, u):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                d.update(u.get("$set", {}))
                return
        self._proj_update(q, u)
    def _proj_update(self, q, u):  # projects fake path
        pass


class _FakeConnector:
    provider = "aws"
    def __init__(self, signals): self._signals = signals
    def discover(self): return self._signals
    def least_privilege_policy(self): return {"Version": "2012-10-17", "Statement": []}


USER = {"id": "u1"}


def _patch(monkeypatch, signals=None, raise_exc=None):
    disc, projects = _Col(), _Col()
    projects.insert_one({"id": "p1", "user_id": "u1", "name": "P1"})
    monkeypatch.setattr(C, "discoveries_collection", lambda: disc)
    monkeypatch.setattr(C, "projects_collection", lambda: projects)
    monkeypatch.setattr(C, "get_project_for_user", lambda pid, uid: {"id": pid, "user_id": uid})
    monkeypatch.setattr(C, "insert_audit_log", lambda *a, **k: None)

    def fake_get_connector(provider, **kwargs):
        if raise_exc:
            raise raise_exc
        # assert credentials were filtered — no client_factory/http_get leaks through
        assert "client_factory" not in kwargs and "http_get" not in kwargs
        return _FakeConnector(signals or [])
    monkeypatch.setattr(C, "get_connector", fake_get_connector)
    return disc, projects


def _sig(key, value, conf="high"):
    return DiscoveredSignal(key=key, value=value, source="aws", confidence=conf, evidence="e")


def test_catalog_lists_providers(monkeypatch):
    # catalog uses the REAL get_connector for placeholder policies; that needs no network.
    body = _run(C.list_connectors(current_user=USER))
    provs = {p["provider"] for p in body["providers"]}
    assert provs == {"aws", "gcp", "azure", "github"}
    aws = next(p for p in body["providers"] if p["provider"] == "aws")
    assert "least_privilege_policy" in aws and aws["requirements"]


def test_discover_returns_signals_and_suggestions_no_store(monkeypatch):
    disc, _ = _patch(monkeypatch, signals=[_sig("has_data_stores", True), _sig("audit_logging_enabled", True)])
    body = _run(C.run_discovery("p1", "aws",
                C.DiscoverRequest(credentials={"role_arn": "arn:x"}, consent_to_store=False), current_user=USER))
    assert body["stored"] is False and body["discovery_id"] is None
    assert any(s["key"] == "has_data_stores" for s in body["signals"])
    assert disc.docs == []  # nothing persisted without consent


def test_discover_persists_with_consent(monkeypatch):
    disc, _ = _patch(monkeypatch, signals=[_sig("has_data_stores", True)])
    body = _run(C.run_discovery("p1", "aws",
                C.DiscoverRequest(credentials={"role_arn": "arn:x"}, consent_to_store=True), current_user=USER))
    assert body["stored"] is True and body["discovery_id"]
    assert len(disc.docs) == 1
    assert "role_arn" not in str(disc.docs[0])  # credentials never persisted


def test_discover_unknown_provider_404(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(C.run_discovery("p1", "oracle", C.DiscoverRequest(credentials={}), current_user=USER))
    assert e.value.status_code == 404


def test_discover_missing_required_credentials_400(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(C.run_discovery("p1", "aws", C.DiscoverRequest(credentials={"region": "ap-south-1"}), current_user=USER))
    assert e.value.status_code == 400  # role_arn missing


def test_discover_connector_error_maps_400(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch, raise_exc=ConnectorError("bad role"))
    with pytest.raises(HTTPException) as e:
        _run(C.run_discovery("p1", "aws", C.DiscoverRequest(credentials={"role_arn": "arn:x"}), current_user=USER))
    assert e.value.status_code == 400


def test_discover_unexpected_error_maps_502(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch, raise_exc=RuntimeError("network down"))
    with pytest.raises(HTTPException) as e:
        _run(C.run_discovery("p1", "aws", C.DiscoverRequest(credentials={"role_arn": "arn:x"}), current_user=USER))
    assert e.value.status_code == 502


def test_apply_merges_suggestions_into_manifest(monkeypatch):
    disc, projects = _patch(monkeypatch, signals=[
        _sig("has_data_stores", True), _sig("audit_logging_enabled", True),
        _sig("storage_encryption", True), _sig("public_access_blocked", True)])
    body = _run(C.run_discovery("p1", "aws",
                C.DiscoverRequest(credentials={"role_arn": "arn:x"}, consent_to_store=True), current_user=USER))
    did = body["discovery_id"]
    applied = _run(C.apply_suggestions("p1", did,
                   C.ApplyRequest(accepted_fields=["storage_locations", "has_security_safeguards"]), current_user=USER))
    assert applied["discovered_manifest"]["storage_locations"] == ["aws"]
    assert applied["discovered_manifest"]["has_security_safeguards"] is True
    # persisted on the project + recorded on the discovery
    assert projects.find_one({"id": "p1"})["discovered_manifest"]["has_security_safeguards"] is True
    assert set(disc.docs[0]["applied_fields"]) == {"storage_locations", "has_security_safeguards"}


def test_apply_unknown_discovery_404(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(C.apply_suggestions("p1", "nope", C.ApplyRequest(accepted_fields=["x"]), current_user=USER))
    assert e.value.status_code == 404


def test_apply_no_matching_fields_400(monkeypatch):
    from fastapi import HTTPException
    disc, _ = _patch(monkeypatch, signals=[_sig("has_data_stores", True)])
    body = _run(C.run_discovery("p1", "aws",
                C.DiscoverRequest(credentials={"role_arn": "arn:x"}, consent_to_store=True), current_user=USER))
    with pytest.raises(HTTPException) as e:
        _run(C.apply_suggestions("p1", body["discovery_id"],
             C.ApplyRequest(accepted_fields=["nonexistent_field"]), current_user=USER))
    assert e.value.status_code == 400


def test_list_and_get_discovery(monkeypatch):
    _patch(monkeypatch, signals=[_sig("has_data_stores", True)])
    body = _run(C.run_discovery("p1", "aws",
                C.DiscoverRequest(credentials={"role_arn": "arn:x"}, consent_to_store=True), current_user=USER))
    listed = _run(C.list_discoveries("p1", current_user=USER))
    assert listed["count"] == 1 and listed["discoveries"][0]["provider"] == "aws"
    detail = _run(C.get_discovery("p1", body["discovery_id"], current_user=USER))
    assert detail["provider"] == "aws" and "signals" in detail
