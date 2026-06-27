"""Monitoring API + history persistence (Phase 2.1/2.2).

Handlers exercised directly (no TestClient), with fake collections, matching the
test_readiness_api.py pattern.
"""

import asyncio
import datetime as dt

import saas.app.monitoring as M


def _run(coro):
    return asyncio.run(coro)


def _matches(doc, query):
    for key, cond in query.items():
        val = doc.get(key)
        if isinstance(cond, dict):
            if "$lt" in cond and not (val is not None and val < cond["$lt"]):
                return False
            if "$gte" in cond and not (val is not None and val >= cond["$gte"]):
                return False
        elif val != cond:
            return False
    return True


class _Cursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, field, direction):
        self._docs.sort(key=lambda d: d.get(field), reverse=direction < 0)
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    def __iter__(self):
        return iter(self._docs)


class _FakeRuns:
    def __init__(self):
        self.docs = []

    def insert_one(self, doc):
        self.docs.append(doc)

    def find(self, query):
        return _Cursor([d for d in self.docs if _matches(d, query)])

    def find_one(self, query, sort=None):
        matched = [d for d in self.docs if _matches(d, query)]
        if sort:
            field, direction = sort[0]
            matched.sort(key=lambda d: d.get(field), reverse=direction < 0)
        return matched[0] if matched else None

    def count_documents(self, query):
        return sum(1 for d in self.docs if _matches(d, query))


def _patch(monkeypatch):
    fake = _FakeRuns()
    monkeypatch.setattr(M, "scan_runs_collection", lambda: fake)
    # Bypass ownership lookup (DB-backed) — auth is covered elsewhere.
    monkeypatch.setattr(M, "get_project_for_user", lambda pid, uid: {"id": pid, "user_id": uid})
    return fake


def _findings(*pairs):
    return {"results": [{"rule_id": rid, "status": st, "title": rid, "severity": "medium"} for rid, st in pairs]}


def _seed_run(fake, scan_id, when, findings, summary):
    M.record_scan_run(
        {"id": scan_id, "project_id": "p1", "user_id": "u1", "scan_name": scan_id, "rulepack_version": "rp",
         "results_count": len(findings["results"])},
        findings,
        summary,
        when,
        source="test",
    )


USER = {"id": "u1"}


def test_record_scan_run_stores_compact_snapshot(monkeypatch):
    fake = _patch(monkeypatch)
    run = M.record_scan_run(
        {"id": "s1", "project_id": "p1", "user_id": "u1", "scan_name": "s1", "rulepack_version": "rp", "results_count": 2},
        _findings(("r1", "PASS"), ("r2", "FAIL")),
        {"passed": 1, "partial": 0, "failed": 1},
        dt.datetime(2026, 6, 1),
        source="test",
    )
    assert run["score"] == 50.0
    assert len(run["rule_states"]) == 2
    assert run["run_id"].startswith("run_")
    assert len(fake.docs) == 1


def test_record_scan_run_skips_without_ids(monkeypatch):
    _patch(monkeypatch)
    assert M.record_scan_run({"id": "s1"}, _findings(("r1", "PASS")), {"passed": 1}, dt.datetime(2026, 6, 1), "test") is None


def test_history_endpoint_lists_newest_first(monkeypatch):
    fake = _patch(monkeypatch)
    _seed_run(fake, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "PASS")), {"passed": 1, "partial": 0, "failed": 0})
    _seed_run(fake, "s2", dt.datetime(2026, 6, 2), _findings(("r1", "FAIL")), {"passed": 0, "partial": 0, "failed": 1})
    body = _run(M.get_scan_history("p1", limit=50, current_user=USER))
    assert body["count"] == 2
    assert body["history"][0]["scan_id"] == "s2"  # newest first
    assert "rule_states" not in body["history"][0]  # snapshot not leaked in timeline


def test_drift_baseline_when_single_scan(monkeypatch):
    fake = _patch(monkeypatch)
    _seed_run(fake, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "PASS")), {"passed": 1, "partial": 0, "failed": 0})
    body = _run(M.get_drift("p1", current_user=USER))
    assert body["baseline"] is True
    assert body["drift"] is None


def test_drift_diffs_latest_two(monkeypatch):
    fake = _patch(monkeypatch)
    _seed_run(fake, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "PASS"), ("r2", "PASS")),
              {"passed": 2, "partial": 0, "failed": 0})
    _seed_run(fake, "s2", dt.datetime(2026, 6, 2), _findings(("r1", "FAIL"), ("r2", "PASS")),
              {"passed": 1, "partial": 0, "failed": 1})
    body = _run(M.get_drift("p1", current_user=USER))
    assert body["baseline"] is False
    assert body["drift"]["has_regression"] is True
    assert body["drift"]["counts"]["regressions"] == 1
    assert body["drift"]["score_delta"] == -50.0


def test_drift_404_when_no_scans(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    try:
        _run(M.get_drift("p1", current_user=USER))
        assert False, "expected 404"
    except HTTPException as e:
        assert e.status_code == 404


def test_summary_reports_regression(monkeypatch):
    fake = _patch(monkeypatch)
    _seed_run(fake, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "PASS")), {"passed": 1, "partial": 0, "failed": 0})
    _seed_run(fake, "s2", dt.datetime(2026, 6, 2), _findings(("r1", "FAIL")), {"passed": 0, "partial": 0, "failed": 1})
    body = _run(M.get_monitoring_summary("p1", current_user=USER))
    assert body["scans_recorded"] == 2
    assert body["latest_score"] == 0.0
    assert body["score_delta"] == -100.0
    assert body["has_regression"] is True
    assert body["open_regressions"] == 1


def test_summary_empty_when_no_scans(monkeypatch):
    _patch(monkeypatch)
    body = _run(M.get_monitoring_summary("p1", current_user=USER))
    assert body["scans_recorded"] == 0
    assert body["latest_score"] is None
    assert body["has_regression"] is False
