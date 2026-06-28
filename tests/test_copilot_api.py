"""Remediation copilot API (Phase 7)."""

import asyncio

import pytest

import saas.app.copilot_api as C


def _run(coro):
    return asyncio.run(coro)


USER = {"id": "u1"}


class _FakeCopilot:
    def __init__(self):
        self.calls = []
    def explain(self, rule, facts):
        self.calls.append(("explain", rule, facts))
        return {"mode": "explain", "grounded": True, "answer": "do X", "disclaimer": "d", "model": "claude-opus-4-8"}
    def draft(self, rule, facts, artifact_type):
        self.calls.append(("draft", rule, facts, artifact_type))
        return {"mode": "draft", "grounded": True, "answer": "DRAFT", "disclaimer": "d", "model": "claude-opus-4-8"}


def _patch(monkeypatch, project=None, copilot=None):
    project = project or {"id": "p1", "user_id": "u1",
                          "discovered_manifest": {"has_privacy_notice": False, "storage_locations": ["aws"]}}
    fake = copilot or _FakeCopilot()
    monkeypatch.setattr(C, "get_project_for_user", lambda pid, uid: project)
    monkeypatch.setattr(C, "get_copilot", lambda: fake)
    monkeypatch.setattr(C, "insert_audit_log", lambda *a, **k: None)
    return fake


RULE_ID = "DPDP-SEC5-NOTICE-001"  # exists in dpdp_india_core_v1


def test_consent_required(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(C.remediate("p1", C.RemediateRequest(rule_id=RULE_ID, consent_to_send=False), current_user=USER))
    assert e.value.status_code == 400


def test_explain_returns_grounded_answer_and_data_sent(monkeypatch):
    fake = _patch(monkeypatch)
    body = _run(C.remediate("p1", C.RemediateRequest(rule_id=RULE_ID, consent_to_send=True), current_user=USER))
    assert body["answer"] == "do X" and body["grounded"] is True
    # only non-PII fact KEYS + citation are echoed (transparency), no values
    assert set(body["data_sent"]["fact_keys"]) == {"has_privacy_notice", "storage_locations"}
    assert body["data_sent"]["rule_citation"]
    # the copilot received the project's confirmed facts
    assert fake.calls[0][0] == "explain"
    assert fake.calls[0][2]["has_privacy_notice"] is False


def test_draft_mode_calls_draft(monkeypatch):
    fake = _patch(monkeypatch)
    body = _run(C.remediate("p1", C.RemediateRequest(
        rule_id=RULE_ID, mode="draft", artifact_type="notice", consent_to_send=True), current_user=USER))
    assert body["mode"] == "draft" and fake.calls[0][0] == "draft"
    assert fake.calls[0][3] == "notice"


def test_bad_mode_400(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(C.remediate("p1", C.RemediateRequest(rule_id=RULE_ID, mode="rewrite", consent_to_send=True), current_user=USER))
    assert e.value.status_code == 400


def test_unknown_rule_404(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(C.remediate("p1", C.RemediateRequest(rule_id="NOPE-001", consent_to_send=True), current_user=USER))
    assert e.value.status_code == 404


def test_unknown_pack_400(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    with pytest.raises(HTTPException) as e:
        _run(C.remediate("p1", C.RemediateRequest(rule_id=RULE_ID, pack_id="bogus", consent_to_send=True), current_user=USER))
    assert e.value.status_code == 400


def test_copilot_failure_maps_502(monkeypatch):
    from fastapi import HTTPException
    class Boom:
        def explain(self, *a): raise RuntimeError("no api key")
    _patch(monkeypatch, copilot=Boom())
    with pytest.raises(HTTPException) as e:
        _run(C.remediate("p1", C.RemediateRequest(rule_id=RULE_ID, consent_to_send=True), current_user=USER))
    assert e.value.status_code == 502
