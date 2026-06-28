"""First-party funnel analytics (Phase 1.6)."""

import asyncio

import saas.app.analytics as A
import saas.app.readiness as R
from saas.app.analytics import score_bucket, record_event
from saas.app.readiness import score_endpoint, ScoreRequest


class _FakeEvents:
    def __init__(self): self.docs = []
    def insert_one(self, doc): self.docs.append(doc)


def _patch_events(monkeypatch):
    fake = _FakeEvents()
    monkeypatch.setattr(A, "events_collection", lambda: fake)
    return fake


def test_score_bucket():
    assert score_bucket(90) == "85-100"
    assert score_bucket(60) == "50-84"
    assert score_bucket(30) == "25-49"
    assert score_bucket(0) == "0-24"


def test_record_event_strips_pii(monkeypatch):
    fake = _patch_events(monkeypatch)
    record_event("x", {"email": "a@b.co", "answers": {"k": 1}, "score_bucket": "0-24"})
    assert len(fake.docs) == 1
    props = fake.docs[0]["props"]
    assert "email" not in props and "answers" not in props
    assert props["score_bucket"] == "0-24"


def test_score_endpoint_emits_completion_event(monkeypatch):
    fake = _patch_events(monkeypatch)
    asyncio.run(score_endpoint(ScoreRequest(answers={"entity_type": "startup"}), user=None))
    events = [d["event"] for d in fake.docs]
    assert "readiness_completed" in events
    # ensure no raw answers leaked into the event
    for d in fake.docs:
        assert "answers" not in d["props"]
