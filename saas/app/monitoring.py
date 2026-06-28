"""Continuous monitoring: scan history & drift detection (Phase 2).

The free CLI is stateless — it scans once and forgets. The paid differentiator is
*memory*: every completed scan is appended to an immutable ``scan_runs`` history per
project, so the dashboard can show posture over time and flag drift (regressions)
between consecutive scans.

This module owns:
  - ``record_scan_run`` — append one compact, immutable run record on scan completion
    (called from the upload/results endpoints in distribution.py), and raise a regression
    alert when the new scan drifted backwards from the previous one.
  - the ``/projects/{id}/monitoring/*`` read API — history timeline, drift diff, summary.
  - per-project monitoring **schedules** + **alerts** (regression + scan-overdue) and the
    ``evaluate_overdue_scans`` sweep that a host cron invokes (saas/app/monitoring_cron.py).

Run records store only a per-rule status snapshot (rule_states) + summary + score, never
raw artefact text, so history stays small and free of uploaded content (DATA_HANDLING.md).
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pymongo import DESCENDING

from compliance.drift import compute_drift, posture_score, rule_states_from_findings
from saas.app.auth import get_current_user
from saas.app.database import get_collection, serialize_document
from saas.app.projects import get_project_for_user, projects_collection

router = APIRouter(prefix="/projects", tags=["monitoring"])

# Schedule cadence -> re-scan interval. "off" disables overdue alerts for a project.
SCHEDULE_INTERVALS: dict[str, dt.timedelta | None] = {
    "off": None,
    "daily": dt.timedelta(days=1),
    "weekly": dt.timedelta(days=7),
    "monthly": dt.timedelta(days=30),
}
HIGH_SEVERITIES = {"high", "critical"}


def scan_runs_collection():
    return get_collection("scan_runs")


def alerts_collection():
    return get_collection("monitor_alerts")


def record_scan_run(
    scan: dict[str, Any],
    findings_json: dict[str, Any] | None,
    summary: dict[str, Any] | None,
    completed_at: dt.datetime,
    source: str,
) -> dict[str, Any] | None:
    """Append an immutable history record for a completed scan.

    Idempotent best-effort: failures here must never break the upload path, so callers
    wrap this and swallow exceptions. Returns the inserted run doc (or None on no-op).

    Side effect: if this scan drifted backwards from the project's previous scan, an
    open ``regression`` alert is raised (deduped per run).
    """
    project_id = scan.get("project_id")
    user_id = scan.get("user_id")
    if not project_id or not user_id:
        return None

    # Capture the prior latest run BEFORE inserting this one, so we can diff for drift.
    prev_run = scan_runs_collection().find_one(
        {"project_id": project_id}, sort=[("created_at", DESCENDING)]
    )

    rule_states = rule_states_from_findings(findings_json)
    score = posture_score(summary)
    run_doc = {
        "run_id": f"run_{uuid.uuid4().hex[:12]}",
        "scan_id": scan.get("id"),
        "project_id": project_id,
        "user_id": user_id,
        "scan_name": scan.get("scan_name"),
        "rulepack_version": scan.get("rulepack_version"),
        "created_at": completed_at,
        "summary": summary or {},
        "results_count": scan.get("results_count", len(rule_states)),
        "score": score,
        "rule_states": rule_states,
        "source": source,
    }
    scan_runs_collection().insert_one(run_doc)

    if prev_run:
        try:
            _raise_regression_alert(prev_run, run_doc)
        except Exception:  # alerting is best-effort; never break ingestion
            pass

    return run_doc


def _raise_regression_alert(prev_run: dict[str, Any], curr_run: dict[str, Any]) -> dict[str, Any] | None:
    """Create a regression alert if the new scan drifted backwards from the previous one."""
    drift = compute_drift(
        prev_run.get("rule_states", []),
        curr_run.get("rule_states", []),
        prev_run.get("score"),
        curr_run.get("score"),
    )
    if not drift["has_regression"]:
        return None

    regressions = drift["regressions"]
    high = [r for r in regressions if str(r.get("severity", "")).lower() in HIGH_SEVERITIES]
    titles = ", ".join(r["title"] for r in regressions[:3])
    if len(regressions) > 3:
        titles += f" (+{len(regressions) - 3} more)"
    delta = drift["score_delta"]
    delta_txt = f" Posture {delta:+.1f} pts." if delta is not None else ""
    return create_alert(
        project_id=curr_run["project_id"],
        user_id=curr_run["user_id"],
        alert_type="regression",
        severity="high" if high else "medium",
        message=f"{len(regressions)} rule(s) regressed since the last scan: {titles}.{delta_txt}",
        detail={
            "run_id": curr_run["run_id"],
            "previous_run_id": prev_run.get("run_id"),
            "regression_count": len(regressions),
            "regressions": regressions,
            "score_delta": delta,
        },
        dedupe_key=f"regression:{curr_run['run_id']}",
    )


def create_alert(
    project_id: str,
    user_id: str,
    alert_type: str,
    severity: str,
    message: str,
    detail: dict[str, Any] | None = None,
    dedupe_key: str | None = None,
    now: dt.datetime | None = None,
) -> dict[str, Any] | None:
    """Insert an alert. If ``dedupe_key`` matches an existing OPEN alert, no-op (returns None)."""
    coll = alerts_collection()
    if dedupe_key and coll.find_one({"dedupe_key": dedupe_key, "status": "open"}):
        return None
    alert = {
        "alert_id": f"alert_{uuid.uuid4().hex[:12]}",
        "project_id": project_id,
        "user_id": user_id,
        "type": alert_type,
        "severity": severity,
        "message": message,
        "detail": detail or {},
        "dedupe_key": dedupe_key,
        "status": "open",
        "created_at": now or dt.datetime.utcnow(),
    }
    coll.insert_one(alert)
    return alert


def _serialize_run(run: dict[str, Any], *, include_states: bool = False) -> dict[str, Any]:
    clean = serialize_document(run)
    if not include_states:
        clean.pop("rule_states", None)
    return clean


def _runs_for_project(project_id: str, limit: int | None = None):
    cursor = scan_runs_collection().find({"project_id": project_id}).sort("created_at", DESCENDING)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


@router.get("/{project_id}/monitoring/history")
async def get_scan_history(
    project_id: str,
    limit: int = 50,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Posture-over-time timeline: one point per completed scan, newest first."""
    get_project_for_user(project_id, current_user["id"])
    limit = max(1, min(limit, 365))
    runs = _runs_for_project(project_id, limit=limit)
    return {
        "project_id": project_id,
        "count": len(runs),
        "history": [_serialize_run(run) for run in runs],
    }


@router.get("/{project_id}/monitoring/drift")
async def get_drift(
    project_id: str,
    from_run: str | None = None,
    to_run: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Drift between two scans. Defaults to the latest two completed runs.

    Pass ``from_run``/``to_run`` (run_ids) to diff a specific pair.
    """
    get_project_for_user(project_id, current_user["id"])
    coll = scan_runs_collection()

    if to_run:
        curr = coll.find_one({"run_id": to_run, "project_id": project_id})
    else:
        curr = coll.find_one({"project_id": project_id}, sort=[("created_at", DESCENDING)])
    if not curr:
        raise HTTPException(status_code=404, detail="No completed scans to compare yet")

    if from_run:
        prev = coll.find_one({"run_id": from_run, "project_id": project_id})
    else:
        prev = coll.find_one(
            {"project_id": project_id, "created_at": {"$lt": curr["created_at"]}},
            sort=[("created_at", DESCENDING)],
        )

    if not prev:
        # Only one scan exists — nothing to diff against. This is a baseline, not an error.
        return {
            "project_id": project_id,
            "baseline": True,
            "message": "First scan on record — no prior scan to compare against.",
            "current": _serialize_run(curr),
            "drift": None,
        }

    drift = compute_drift(
        prev.get("rule_states", []),
        curr.get("rule_states", []),
        prev.get("score"),
        curr.get("score"),
    )
    return {
        "project_id": project_id,
        "baseline": False,
        "previous": _serialize_run(prev),
        "current": _serialize_run(curr),
        "drift": drift,
    }


@router.get("/{project_id}/monitoring/summary")
async def get_monitoring_summary(
    project_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """One-glance posture: latest score, trend vs previous scan, open regressions."""
    project = get_project_for_user(project_id, current_user["id"])
    runs = _runs_for_project(project_id, limit=2)
    open_alerts = alerts_collection().count_documents({"project_id": project_id, "status": "open"})
    schedule = _schedule_of(project)

    if not runs:
        return {
            "project_id": project_id,
            "scans_recorded": 0,
            "latest_score": None,
            "score_delta": None,
            "has_regression": False,
            "open_regressions": 0,
            "open_alerts": open_alerts,
            "last_scan_at": None,
            "schedule": schedule,
            "next_scan_due": None,
        }

    latest = runs[0]
    summary: dict[str, Any] = {
        "project_id": project_id,
        "scans_recorded": scan_runs_collection().count_documents({"project_id": project_id}),
        "latest_score": latest.get("score"),
        "score_delta": None,
        "has_regression": False,
        "open_regressions": 0,
        "open_alerts": open_alerts,
        "last_scan_at": serialize_document(latest.get("created_at")),
        "schedule": schedule,
        "next_scan_due": serialize_document(_next_due(latest.get("created_at"), schedule)),
    }

    if len(runs) >= 2:
        prev = runs[1]
        drift = compute_drift(
            prev.get("rule_states", []),
            latest.get("rule_states", []),
            prev.get("score"),
            latest.get("score"),
        )
        summary["score_delta"] = drift["score_delta"]
        summary["has_regression"] = drift["has_regression"]
        summary["open_regressions"] = drift["counts"]["regressions"]

    return summary


# ── Schedules (2.4) ────────────────────────────────────────────────────────────

def _schedule_of(project: dict[str, Any]) -> str:
    sched = (project or {}).get("monitoring_schedule")
    freq = sched.get("frequency") if isinstance(sched, dict) else None
    return freq if freq in SCHEDULE_INTERVALS else "off"


def _next_due(last_scan_at: dt.datetime | None, schedule: str) -> dt.datetime | None:
    interval = SCHEDULE_INTERVALS.get(schedule)
    if interval is None or last_scan_at is None:
        return None
    return last_scan_at + interval


class ScheduleUpdate(BaseModel):
    frequency: str = Field(description="off | daily | weekly | monthly")


@router.get("/{project_id}/monitoring/schedule")
async def get_schedule(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    project = get_project_for_user(project_id, current_user["id"])
    return {"project_id": project_id, "frequency": _schedule_of(project)}


@router.put("/{project_id}/monitoring/schedule")
async def set_schedule(
    project_id: str,
    body: ScheduleUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Set a project's re-scan cadence. Drives scan-overdue alerts (evaluate_overdue_scans)."""
    get_project_for_user(project_id, current_user["id"])
    freq = body.frequency.strip().lower()
    if freq not in SCHEDULE_INTERVALS:
        raise HTTPException(status_code=400, detail=f"frequency must be one of {sorted(SCHEDULE_INTERVALS)}")
    projects_collection().update_one(
        {"id": project_id},
        {"$set": {"monitoring_schedule": {"frequency": freq, "updated_at": dt.datetime.utcnow()}}},
    )
    return {"project_id": project_id, "frequency": freq}


# ── Alerts (2.4) ───────────────────────────────────────────────────────────────

@router.get("/{project_id}/monitoring/alerts")
async def list_alerts(
    project_id: str,
    status: str = "open",
    limit: int = 50,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """List a project's monitoring alerts (default: open only)."""
    get_project_for_user(project_id, current_user["id"])
    query: dict[str, Any] = {"project_id": project_id}
    if status != "all":
        query["status"] = status
    limit = max(1, min(limit, 200))
    alerts = list(alerts_collection().find(query).sort("created_at", DESCENDING).limit(limit))
    return {"project_id": project_id, "count": len(alerts),
            "alerts": [serialize_document(a) for a in alerts]}


@router.post("/{project_id}/monitoring/alerts/{alert_id}/ack")
async def acknowledge_alert(
    project_id: str,
    alert_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Acknowledge (close) an open alert."""
    get_project_for_user(project_id, current_user["id"])
    result = alerts_collection().update_one(
        {"alert_id": alert_id, "project_id": project_id},
        {"$set": {"status": "acknowledged", "acknowledged_at": dt.datetime.utcnow()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert_id": alert_id, "status": "acknowledged"}


# ── Scan-overdue sweep (2.4 cron entrypoint) ───────────────────────────────────

def evaluate_overdue_scans(now: dt.datetime | None = None) -> list[dict[str, Any]]:
    """Raise a scan-overdue alert for every scheduled project whose last scan is stale.

    Idempotent per UTC day via a dedupe key, so re-running the cron does not spam alerts.
    Returns the alerts created this sweep. Invoked by saas/app/monitoring_cron.py.
    """
    now = now or dt.datetime.utcnow()
    created: list[dict[str, Any]] = []
    cursor = projects_collection().find({"monitoring_schedule.frequency": {"$in": ["daily", "weekly", "monthly"]}})
    for project in cursor:
        schedule = _schedule_of(project)
        interval = SCHEDULE_INTERVALS.get(schedule)
        if interval is None:
            continue
        project_id = project.get("id")
        latest = scan_runs_collection().find_one({"project_id": project_id}, sort=[("created_at", DESCENDING)])
        last_at = latest.get("created_at") if latest else None
        overdue = last_at is None or (now - last_at) > interval
        if not overdue:
            continue
        last_txt = "never scanned" if last_at is None else f"last scan {last_at.date().isoformat()}"
        alert = create_alert(
            project_id=project_id,
            user_id=project.get("user_id"),
            alert_type="scan_overdue",
            severity="medium",
            message=f"Re-scan overdue for '{project.get('name', project_id)}' ({schedule} cadence; {last_txt}).",
            detail={"schedule": schedule, "last_scan_at": serialize_document(last_at)},
            dedupe_key=f"overdue:{project_id}:{now.date().isoformat()}",
            now=now,
        )
        if alert:
            created.append(alert)
    return created
