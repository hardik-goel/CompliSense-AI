"""Evidence export API (Phase 8)."""

import asyncio

import saas.app.evidence_api as E


def _run(coro):
    return asyncio.run(coro)


USER = {"id": "u1", "email": "owner@x.com"}
PROJECT = {"id": "p1", "name": "Acme", "compliance_standard": "DPDP_INDIA",
           "discovered_manifest": {"has_privacy_notice": True, "has_security_safeguards": True}}


def _patch(monkeypatch, role="owner"):
    monkeypatch.setattr(E, "get_project_with_role", lambda pid, user, action: (PROJECT, role))
    monkeypatch.setattr(E, "_runs", lambda pid: [{"created_at": "2026-06-02", "score": 70, "scan_id": "s1"}])
    monkeypatch.setattr(E, "_alerts", lambda pid: [{"status": "open", "message": "regressed"}])
    monkeypatch.setattr(E, "_discoveries", lambda pid: [{"provider": "aws", "signals": [1], "suggestions": [], "applied_fields": []}])
    monkeypatch.setattr(E, "_pii", lambda pid: [{"report": {"category_to_sources": {"email": ["db"]}, "has_cross_border": False}}])


def test_evidence_json_assembles_with_real_readiness(monkeypatch):
    _patch(monkeypatch)
    pack = _run(E.get_evidence("p1", current_user=USER))
    assert pack["meta"]["project_name"] == "Acme"
    assert "readiness" in pack and "score" in pack["readiness"]
    assert pack["citations"]  # real DPDP rules carry citations
    assert pack["pii_data_flow"]["categories"] == ["email"]
    assert pack["meta"]["prepared_by"] == "owner@x.com"


def test_evidence_html_is_downloadable_document(monkeypatch):
    _patch(monkeypatch)
    resp = _run(E.export_evidence_html("p1", current_user=USER))
    assert resp.media_type == "text/html"
    assert "attachment" in resp.headers["content-disposition"]
    body = resp.body.decode()
    assert "Acme" in body and "Evidence Pack" in body and "not legal advice" in body.lower()


def test_security_safeguards_reflected_in_readiness(monkeypatch):
    _patch(monkeypatch)
    pack = _run(E.get_evidence("p1", current_user=USER))
    # has_security_safeguards=True ⇒ that rule is READY, not a gap
    ready_ids = {r["rule_id"] for r in pack["readiness"]["ready"]}
    assert "DPDP-SEC8-OBLIGATIONS-001" in ready_ids
