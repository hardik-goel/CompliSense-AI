"""Public DPDP Readiness API (Phase 1.3).

Handlers are exercised directly (no TestClient) to avoid an httpx test dependency.
"""

import asyncio

from saas.app.readiness import score_endpoint, get_questionnaire_endpoint, ScoreRequest


GOOD_ANSWERS = {
    "entity_type": "startup",
    "has_privacy_notice": False,
    "consent_mechanism": "none",
    "has_withdrawal_mechanism": False,
    "has_security_safeguards": False,
    "has_breach_process": False,
    "has_grievance_contact": False,
    "notified_as_sdf": False,
    "processes_children_data": False,
}


def _run(coro):
    return asyncio.run(coro)


def test_questionnaire_endpoint():
    body = _run(get_questionnaire_endpoint())
    assert len(body["questions"]) > 5


def test_anonymous_gets_teaser_not_full_report():
    body = _run(score_endpoint(ScoreRequest(answers=GOOD_ANSWERS), user=None))
    assert "readiness_score" in body
    assert body["full_report"] is False
    assert len(body["top_gaps"]) <= 3
    assert "gaps" not in body  # full list gated
    assert body["signup_required_for_full_report"] is True
    assert "not legal advice" in body["disclaimer"].lower()


def test_authenticated_gets_full_report():
    body = _run(score_endpoint(ScoreRequest(answers=GOOD_ANSWERS), user={"id": "u1"}))
    assert body["full_report"] is True
    assert "gaps" in body
    assert body["authenticated"] is True


def test_bad_pack_rejected():
    from fastapi import HTTPException
    try:
        _run(score_endpoint(ScoreRequest(answers=GOOD_ANSWERS, pack_id="euai_core_v1"), user=None))
        assert False, "expected HTTPException"
    except HTTPException as e:
        assert e.status_code == 400


def test_score_is_honest_zero_for_empty_posture():
    body = _run(score_endpoint(ScoreRequest(answers={"entity_type": "startup"}), user=None))
    assert body["readiness_score"] == 0


# ── Persistence + auth gating (Phase 1.5) ──────────────────────────────────────

import saas.app.readiness as R


class _Cursor:
    def __init__(self, docs): self._docs = docs
    def sort(self, *a, **k): return list(self._docs)


class _FakeCollection:
    def __init__(self): self.docs = []
    def insert_one(self, doc): self.docs.append(doc)
    def find(self, query): return _Cursor([d for d in self.docs if all(d.get(k) == v for k, v in query.items())])
    def find_one(self, query): return next((d for d in self.docs if all(d.get(k) == v for k, v in query.items())), None)


def _patch_collection(monkeypatch):
    fake = _FakeCollection()
    monkeypatch.setattr(R, "assessments_collection", lambda: fake)
    return fake


def test_signed_in_with_consent_persists(monkeypatch):
    fake = _patch_collection(monkeypatch)
    body = _run(score_endpoint(ScoreRequest(answers=GOOD_ANSWERS, consent_to_store=True), user={"id": "u1"}))
    assert body["saved"] is True
    assert len(fake.docs) == 1
    assert fake.docs[0]["user_id"] == "u1"


def test_signed_in_without_consent_does_not_persist(monkeypatch):
    fake = _patch_collection(monkeypatch)
    body = _run(score_endpoint(ScoreRequest(answers=GOOD_ANSWERS, consent_to_store=False), user={"id": "u1"}))
    assert body["saved"] is False
    assert fake.docs == []


def test_anonymous_never_persists_even_with_consent(monkeypatch):
    fake = _patch_collection(monkeypatch)
    body = _run(score_endpoint(ScoreRequest(answers=GOOD_ANSWERS, consent_to_store=True), user=None))
    assert "saved" not in body  # ephemeral path
    assert fake.docs == []


def test_list_and_get_assessment(monkeypatch):
    fake = _patch_collection(monkeypatch)
    _run(score_endpoint(ScoreRequest(answers=GOOD_ANSWERS, consent_to_store=True), user={"id": "u1"}))
    listed = _run(R.list_assessments(user={"id": "u1"}))
    assert len(listed["assessments"]) == 1
    aid = fake.docs[0]["id"]
    detail = _run(R.get_assessment(aid, user={"id": "u1"}))
    assert "report" in detail and "readiness_score" in detail["report"]


def test_get_assessment_404_for_other_user(monkeypatch):
    from fastapi import HTTPException
    _patch_collection(monkeypatch)
    _run(score_endpoint(ScoreRequest(answers=GOOD_ANSWERS, consent_to_store=True), user={"id": "u1"}))
    try:
        _run(R.get_assessment("nonexistent", user={"id": "u2"}))
        assert False
    except HTTPException as e:
        assert e.status_code == 404


# ── Admin-gated analytics summary (item 3) ─────────────────────────────────────

from saas.app.readiness import require_admin, analytics_summary
from saas.app.config import settings as _settings


def test_require_admin_rejects_missing_and_bad_token():
    from fastapi import HTTPException
    for bad in (None, "wrong-token"):
        try:
            _run(require_admin(x_admin_api_token=bad))
            assert False, "expected 403"
        except HTTPException as e:
            assert e.status_code == 403


def test_require_admin_accepts_valid_token():
    assert _run(require_admin(x_admin_api_token=_settings.admin_api_token)) is True
