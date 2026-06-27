"""Continuous monitoring: scan history & drift detection (Phase 2).

The free CLI is stateless — it scans once and forgets. The paid differentiator is
*memory*: every completed scan is appended to an immutable ``scan_runs`` history per
project, so the dashboard can show posture over time and flag drift (regressions)
between consecutive scans.

This module owns:
  - ``record_scan_run`` — append one compact, immutable run record on scan completion
    (called from the upload/results endpoints in distribution.py).
  - the ``/projects/{id}/monitoring/*`` read API — history timeline, drift diff, summary.

Run records store only a per-rule status snapshot (rule_states) + summary + score, never
raw artefact text, so history stays small and free of uploaded content (DATA_HANDLING.md).
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pymongo import DESCENDING

from compliance.drift import compute_drift, posture_score, rule_states_from_findings
from saas.app.auth import get_current_user
from saas.app.database import get_collection, serialize_document
from saas.app.projects import get_project_for_user

router = APIRouter(prefix="/projects", tags=["monitoring"])


def scan_runs_collection():
    return get_collection("scan_runs")


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
    """
    project_id = scan.get("project_id")
    user_id = scan.get("user_id")
    if not project_id or not user_id:
        return None

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
    return run_doc


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
    get_project_for_user(project_id, current_user["id"])
    runs = _runs_for_project(project_id, limit=2)

    if not runs:
        return {
            "project_id": project_id,
            "scans_recorded": 0,
            "latest_score": None,
            "score_delta": None,
            "has_regression": False,
            "open_regressions": 0,
            "last_scan_at": None,
        }

    latest = runs[0]
    summary: dict[str, Any] = {
        "project_id": project_id,
        "scans_recorded": scan_runs_collection().count_documents({"project_id": project_id}),
        "latest_score": latest.get("score"),
        "score_delta": None,
        "has_regression": False,
        "open_regressions": 0,
        "last_scan_at": serialize_document(latest.get("created_at")),
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
