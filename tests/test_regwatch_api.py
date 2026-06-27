"""Regulatory-change watcher API (Phase 5.2/5.3)."""

import asyncio
import datetime as dt

import pytest

import saas.app.regwatch_api as R


def _run(coro):
    return asyncio.run(coro)


class _Col:
    def __init__(self): self.docs = []
    def insert_one(self, d): self.docs.append(d)
    def find(self, q):
        class C(list):
            def sort(self, *a, **k): return self
        return C([d for d in self.docs if all(d.get(k) == v for k, v in q.items())])
    def find_one(self, q, sort=None):
        matched = [d for d in self.docs if all(d.get(k) == v for k, v in q.items())]
        if sort:
            f, dirn = sort[0]
            matched.sort(key=lambda x: x.get(f), reverse=dirn < 0)
        return matched[0] if matched else None
    def update_one(self, q, u):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                d.update(u.get("$set", {})); return


SOURCES = [{"url": "https://law/a", "rule_ids": ["R1"], "pack_ids": ["p"]},
           {"url": "https://law/b", "rule_ids": ["R2"], "pack_ids": ["p"]}]


def _patch(monkeypatch, pages):
    snaps, changes = _Col(), _Col()
    monkeypatch.setattr(R, "snapshots_collection", lambda: snaps)
    monkeypatch.setattr(R, "changes_collection", lambda: changes)
    monkeypatch.setattr(R, "watch_sources", lambda: SOURCES)
    monkeypatch.setattr(R, "insert_audit_log", lambda *a, **k: None)
    fetcher = lambda url: pages[url]
    return snaps, changes, fetcher


NOW1 = dt.datetime(2026, 6, 1)
NOW2 = dt.datetime(2026, 6, 8)


def test_first_sweep_is_baseline_no_changes(monkeypatch):
    snaps, changes, fetcher = _patch(monkeypatch, {"https://law/a": "v1", "https://law/b": "v1"})
    summary = R.run_watch_sweep(fetcher=fetcher, now=NOW1)
    assert summary["checked"] == 2 and summary["changes_created"] == 0
    assert len(snaps.docs) == 2 and changes.docs == []


def test_change_detected_on_second_sweep(monkeypatch):
    snaps, changes, fetcher = _patch(monkeypatch, {"https://law/a": "v1", "https://law/b": "v1"})
    R.run_watch_sweep(fetcher=fetcher, now=NOW1)
    # source a changes; b unchanged
    fetcher2 = lambda url: {"https://law/a": "v2-AMENDED", "https://law/b": "v1"}[url]
    summary = R.run_watch_sweep(fetcher=fetcher2, now=NOW2)
    assert summary["changes_created"] == 1
    chg = changes.docs[0]
    assert chg["url"] == "https://law/a" and chg["status"] == "pending"
    assert chg["rule_ids"] == ["R1"]


def test_change_deduped_while_pending(monkeypatch):
    _, changes, fetcher = _patch(monkeypatch, {"https://law/a": "v1", "https://law/b": "v1"})
    R.run_watch_sweep(fetcher=fetcher, now=NOW1)
    f2 = lambda url: {"https://law/a": "v2", "https://law/b": "v1"}[url]
    R.run_watch_sweep(fetcher=f2, now=NOW2)
    R.run_watch_sweep(fetcher=f2, now=dt.datetime(2026, 6, 15))  # same new hash, still pending
    assert len(changes.docs) == 1  # not duplicated


def test_fetch_error_is_recorded_not_fatal(monkeypatch):
    snaps, changes, _ = _patch(monkeypatch, {})
    def boom(url):
        if url == "https://law/a":
            raise RuntimeError("timeout")
        return "ok"
    summary = R.run_watch_sweep(fetcher=boom, now=NOW1)
    assert summary["checked"] == 1 and len(summary["errors"]) == 1
    assert summary["errors"][0]["url"] == "https://law/a"


def test_review_requires_valid_decision(monkeypatch):
    from fastapi import HTTPException
    _, changes, fetcher = _patch(monkeypatch, {"https://law/a": "v1", "https://law/b": "v1"})
    changes.insert_one({"change_id": "c1", "url": "u", "rule_ids": ["R1"], "status": "pending"})
    with pytest.raises(HTTPException) as e:
        _run(R.review_change("c1", R.ReviewRequest(decision="maybe"), _admin=True))
    assert e.value.status_code == 400


def test_review_approve_marks_and_returns_rules(monkeypatch):
    _, changes, _ = _patch(monkeypatch, {})
    changes.insert_one({"change_id": "c1", "url": "u", "rule_ids": ["R1", "R2"], "status": "pending"})
    out = _run(R.review_change("c1", R.ReviewRequest(decision="approved", note="amended"), _admin=True))
    assert out["status"] == "approved" and out["rules_to_review"] == ["R1", "R2"]
    assert changes.docs[0]["status"] == "approved" and changes.docs[0]["note"] == "amended"


def test_review_unknown_change_404(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch, {})
    with pytest.raises(HTTPException) as e:
        _run(R.review_change("nope", R.ReviewRequest(decision="dismissed"), _admin=True))
    assert e.value.status_code == 404


def test_list_changes_filters_status(monkeypatch):
    _, changes, _ = _patch(monkeypatch, {})
    changes.insert_one({"change_id": "c1", "status": "pending", "detected_at": NOW1})
    changes.insert_one({"change_id": "c2", "status": "approved", "detected_at": NOW2})
    pending = _run(R.list_changes(status="pending", current_user={"id": "u1"}))
    assert pending["count"] == 1 and pending["changes"][0]["change_id"] == "c1"


def test_watch_sources_derived_from_real_packs():
    # integration: the real rulepacks yield watched source URLs mapped to rules.
    sources = R.watch_sources()
    assert sources and all("url" in s and s["rule_ids"] for s in sources)
