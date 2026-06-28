"""Monitoring API + history persistence (Phase 2.1/2.2).

Handlers exercised directly (no TestClient), with fake collections, matching the
test_readiness_api.py pattern.
"""

import asyncio
import datetime as dt

import saas.app.monitoring as M


def _run(coro):
    return asyncio.run(coro)


def _get_path(doc, dotted):
    cur = doc
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _matches(doc, query):
    for key, cond in query.items():
        val = _get_path(doc, key) if "." in key else doc.get(key)
        if isinstance(cond, dict):
            if "$lt" in cond and not (val is not None and val < cond["$lt"]):
                return False
            if "$gte" in cond and not (val is not None and val >= cond["$gte"]):
                return False
            if "$in" in cond and val not in cond["$in"]:
                return False
        elif val != cond:
            return False
    return True


class _Cursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, field, direction):
        self._docs.sort(key=lambda d: (d.get(field) is None, d.get(field)), reverse=direction < 0)
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    def __iter__(self):
        return iter(self._docs)


class _UpdateResult:
    def __init__(self, matched):
        self.matched_count = matched


class _FakeCol:
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
            matched.sort(key=lambda d: (d.get(field) is None, d.get(field)), reverse=direction < 0)
        return matched[0] if matched else None

    def count_documents(self, query):
        return sum(1 for d in self.docs if _matches(d, query))

    def update_one(self, query, update, upsert=False):
        matched = [d for d in self.docs if _matches(d, query)]
        if matched:
            matched[0].update(update.get("$set", {}))
            return _UpdateResult(1)
        if upsert:
            new = {**{k: v for k, v in query.items() if not isinstance(v, dict)}, **update.get("$set", {})}
            self.docs.append(new)
        return _UpdateResult(0)


def _patch(monkeypatch):
    runs, alerts, projects = _FakeCol(), _FakeCol(), _FakeCol()
    monkeypatch.setattr(M, "scan_runs_collection", lambda: runs)
    monkeypatch.setattr(M, "alerts_collection", lambda: alerts)
    monkeypatch.setattr(M, "projects_collection", lambda: projects)
    # Bypass ownership lookup (DB-backed) — auth is covered elsewhere.
    monkeypatch.setattr(M, "get_project_for_user",
                        lambda pid, uid: projects.find_one({"id": pid}) or {"id": pid, "user_id": uid})
    return runs, alerts, projects


def _findings(*pairs):
    return {"results": [{"rule_id": rid, "status": st, "title": rid, "severity": "medium"} for rid, st in pairs]}


def _seed_run(runs, scan_id, when, findings, summary):
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
    runs, _alerts, _projects = _patch(monkeypatch)
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
    assert len(runs.docs) == 1


def test_record_scan_run_skips_without_ids(monkeypatch):
    _patch(monkeypatch)
    assert M.record_scan_run({"id": "s1"}, _findings(("r1", "PASS")), {"passed": 1}, dt.datetime(2026, 6, 1), "test") is None


def test_history_endpoint_lists_newest_first(monkeypatch):
    runs, _alerts, _projects = _patch(monkeypatch)
    _seed_run(runs, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "PASS")), {"passed": 1, "partial": 0, "failed": 0})
    _seed_run(runs, "s2", dt.datetime(2026, 6, 2), _findings(("r1", "FAIL")), {"passed": 0, "partial": 0, "failed": 1})
    body = _run(M.get_scan_history("p1", limit=50, current_user=USER))
    assert body["count"] == 2
    assert body["history"][0]["scan_id"] == "s2"  # newest first
    assert "rule_states" not in body["history"][0]  # snapshot not leaked in timeline


def test_drift_baseline_when_single_scan(monkeypatch):
    runs, _alerts, _projects = _patch(monkeypatch)
    _seed_run(runs, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "PASS")), {"passed": 1, "partial": 0, "failed": 0})
    body = _run(M.get_drift("p1", current_user=USER))
    assert body["baseline"] is True
    assert body["drift"] is None


def test_drift_diffs_latest_two(monkeypatch):
    runs, _alerts, _projects = _patch(monkeypatch)
    _seed_run(runs, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "PASS"), ("r2", "PASS")),
              {"passed": 2, "partial": 0, "failed": 0})
    _seed_run(runs, "s2", dt.datetime(2026, 6, 2), _findings(("r1", "FAIL"), ("r2", "PASS")),
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
    runs, _alerts, _projects = _patch(monkeypatch)
    _seed_run(runs, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "PASS")), {"passed": 1, "partial": 0, "failed": 0})
    _seed_run(runs, "s2", dt.datetime(2026, 6, 2), _findings(("r1", "FAIL")), {"passed": 0, "partial": 0, "failed": 1})
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


# ── 2.4: regression alert on completion ────────────────────────────────────────

def test_regression_on_completion_raises_alert(monkeypatch):
    runs, alerts, _projects = _patch(monkeypatch)
    _seed_run(runs, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "PASS")), {"passed": 1, "partial": 0, "failed": 0})
    _seed_run(runs, "s2", dt.datetime(2026, 6, 2), _findings(("r1", "FAIL")), {"passed": 0, "partial": 0, "failed": 1})
    assert len(alerts.docs) == 1
    a = alerts.docs[0]
    assert a["type"] == "regression" and a["status"] == "open"
    assert a["detail"]["regression_count"] == 1


def test_first_scan_raises_no_alert(monkeypatch):
    runs, alerts, _projects = _patch(monkeypatch)
    _seed_run(runs, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "FAIL")), {"passed": 0, "partial": 0, "failed": 1})
    assert alerts.docs == []  # nothing to drift from


def test_improvement_only_raises_no_alert(monkeypatch):
    runs, alerts, _projects = _patch(monkeypatch)
    _seed_run(runs, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "FAIL")), {"passed": 0, "partial": 0, "failed": 1})
    _seed_run(runs, "s2", dt.datetime(2026, 6, 2), _findings(("r1", "PASS")), {"passed": 1, "partial": 0, "failed": 0})
    assert alerts.docs == []


def test_high_severity_regression_marked_high(monkeypatch):
    runs, alerts, _projects = _patch(monkeypatch)
    hi = lambda st: {"results": [{"rule_id": "r1", "status": st, "title": "Breach rule", "severity": "high"}]}
    M.record_scan_run({"id": "s1", "project_id": "p1", "user_id": "u1"}, hi("PASS"),
                      {"passed": 1, "partial": 0, "failed": 0}, dt.datetime(2026, 6, 1), "test")
    M.record_scan_run({"id": "s2", "project_id": "p1", "user_id": "u1"}, hi("FAIL"),
                      {"passed": 0, "partial": 0, "failed": 1}, dt.datetime(2026, 6, 2), "test")
    assert alerts.docs[0]["severity"] == "high"


# ── 2.4: schedule ──────────────────────────────────────────────────────────────

def test_set_and_get_schedule(monkeypatch):
    _runs, _alerts, projects = _patch(monkeypatch)
    projects.insert_one({"id": "p1", "user_id": "u1", "name": "P1"})
    body = _run(M.set_schedule("p1", M.ScheduleUpdate(frequency="weekly"), current_user=USER))
    assert body["frequency"] == "weekly"
    got = _run(M.get_schedule("p1", current_user=USER))
    assert got["frequency"] == "weekly"


def test_set_schedule_rejects_bad_frequency(monkeypatch):
    from fastapi import HTTPException
    _runs, _alerts, projects = _patch(monkeypatch)
    projects.insert_one({"id": "p1", "user_id": "u1", "name": "P1"})
    try:
        _run(M.set_schedule("p1", M.ScheduleUpdate(frequency="hourly"), current_user=USER))
        assert False, "expected 400"
    except HTTPException as e:
        assert e.status_code == 400


# ── 2.4: alerts list + ack ─────────────────────────────────────────────────────

def test_list_and_ack_alert(monkeypatch):
    _runs, alerts, _projects = _patch(monkeypatch)
    M.create_alert("p1", "u1", "regression", "high", "boom", dedupe_key="k1")
    listed = _run(M.list_alerts("p1", current_user=USER))
    assert listed["count"] == 1
    aid = alerts.docs[0]["alert_id"]
    _run(M.acknowledge_alert("p1", aid, current_user=USER))
    assert alerts.docs[0]["status"] == "acknowledged"
    assert _run(M.list_alerts("p1", current_user=USER))["count"] == 0  # only open by default


def test_ack_unknown_alert_404(monkeypatch):
    from fastapi import HTTPException
    _patch(monkeypatch)
    try:
        _run(M.acknowledge_alert("p1", "nope", current_user=USER))
        assert False
    except HTTPException as e:
        assert e.status_code == 404


def test_create_alert_dedupes_open(monkeypatch):
    _runs, alerts, _projects = _patch(monkeypatch)
    assert M.create_alert("p1", "u1", "regression", "high", "x", dedupe_key="k") is not None
    assert M.create_alert("p1", "u1", "regression", "high", "x", dedupe_key="k") is None  # deduped
    assert len(alerts.docs) == 1


# ── 2.4: overdue sweep (cron) ──────────────────────────────────────────────────

def test_overdue_sweep_flags_stale_scheduled_project(monkeypatch):
    runs, alerts, projects = _patch(monkeypatch)
    projects.insert_one({"id": "p1", "user_id": "u1", "name": "P1",
                         "monitoring_schedule": {"frequency": "weekly"}})
    _seed_run(runs, "s1", dt.datetime(2026, 6, 1), _findings(("r1", "PASS")), {"passed": 1, "partial": 0, "failed": 0})
    created = M.evaluate_overdue_scans(now=dt.datetime(2026, 6, 20))  # 19 days > 7
    assert len(created) == 1
    assert created[0]["type"] == "scan_overdue"
    # idempotent within a day
    assert M.evaluate_overdue_scans(now=dt.datetime(2026, 6, 20)) == []


def test_overdue_sweep_skips_fresh_and_off(monkeypatch):
    runs, _alerts, projects = _patch(monkeypatch)
    projects.insert_one({"id": "fresh", "user_id": "u1", "name": "F", "monitoring_schedule": {"frequency": "weekly"}})
    projects.insert_one({"id": "off", "user_id": "u1", "name": "O", "monitoring_schedule": {"frequency": "off"}})
    M.record_scan_run({"id": "s1", "project_id": "fresh", "user_id": "u1"}, _findings(("r1", "PASS")),
                      {"passed": 1, "partial": 0, "failed": 0}, dt.datetime(2026, 6, 19), "test")
    created = M.evaluate_overdue_scans(now=dt.datetime(2026, 6, 20))  # 1 day < 7, and 'off' excluded
    assert created == []


def test_overdue_sweep_flags_never_scanned(monkeypatch):
    _runs, _alerts, projects = _patch(monkeypatch)
    projects.insert_one({"id": "p1", "user_id": "u1", "name": "P1", "monitoring_schedule": {"frequency": "daily"}})
    created = M.evaluate_overdue_scans(now=dt.datetime(2026, 6, 20))
    assert len(created) == 1 and "never scanned" in created[0]["message"]
