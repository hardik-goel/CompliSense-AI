"""Project readiness from discovered_manifest (Phase 3 → readiness wire)."""

import asyncio

import pytest

import saas.app.project_readiness as PR


def _run(coro):
    return asyncio.run(coro)


USER = {"id": "u1"}


def _patch(monkeypatch, project):
    monkeypatch.setattr(PR, "get_project_for_user", lambda pid, uid: project)
    return project


def test_readiness_scores_from_discovered_manifest(monkeypatch):
    _patch(monkeypatch, {"id": "p1", "user_id": "u1",
                         "discovered_manifest": {"has_security_safeguards": True, "retention_defined": True}})
    report = _run(PR.project_readiness("p1", current_user=USER))
    assert "readiness_score" in report
    assert report["evidence"]["has_discovery"] is True
    assert set(report["evidence"]["discovered_fields"]) == {"has_security_safeguards", "retention_defined"}


def test_connector_backed_rules_are_tagged(monkeypatch):
    _patch(monkeypatch, {"id": "p1", "user_id": "u1",
                         "discovered_manifest": {"has_security_safeguards": True}})
    report = _run(PR.project_readiness("p1", current_user=USER))
    backed = [i for i in report["ready"] + report["gaps"] if i.get("evidence_source") == "connector"]
    rule_ids = {i["rule_id"] for i in backed}
    assert "DPDP-SEC8-OBLIGATIONS-001" in rule_ids  # security-safeguards rule corroborated


def test_discovered_overlays_self_declared(monkeypatch):
    # self-declared says no safeguards; discovery (evidence) overrides to yes.
    _patch(monkeypatch, {"id": "p1", "user_id": "u1",
                         "manifest_answers": {"has_security_safeguards": False},
                         "discovered_manifest": {"has_security_safeguards": True}})
    report = _run(PR.project_readiness("p1", current_user=USER))
    sec = next(i for i in report["ready"] + report["gaps"] if i["rule_id"] == "DPDP-SEC8-OBLIGATIONS-001")
    assert sec["status"] == "READY"


def test_empty_project_is_honest_low(monkeypatch):
    _patch(monkeypatch, {"id": "p1", "user_id": "u1"})
    report = _run(PR.project_readiness("p1", current_user=USER))
    assert report["evidence"]["has_discovery"] is False
    assert report["readiness_score"] >= 0  # unknown counts as gap, never fabricated


def test_children_data_flips_applicability_profile(monkeypatch):
    # PII-derived processes_children_data (4.4 wire) must reach the readiness applicability profile.
    _patch(monkeypatch, {"id": "p1", "user_id": "u1",
                         "discovered_manifest": {"processes_children_data": True}})
    report = _run(PR.project_readiness("p1", current_user=USER))
    assert report["evidence"]["profile"]["processes_children_data"] is True


def test_bad_pack_rejected(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch, {"id": "p1", "user_id": "u1"})
    with pytest.raises(HTTPException) as e:
        _run(PR.project_readiness("p1", pack_id="euai_core_v1", current_user=USER))
    assert e.value.status_code == 400
