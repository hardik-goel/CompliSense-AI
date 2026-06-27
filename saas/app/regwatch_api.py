"""Regulatory-change watcher API (Phase 5.2/5.3).

Wires the regwatch core (compliance/regwatch.py) to persistence + a human-gated review
workflow. A sweep fetches each watched legal source, hashes it, and — if it changed since
the last snapshot — raises a PENDING change for a human to review. Approving/dismissing a
change is a governance action (audited); it NEVER edits a rulepack or rescores anyone.

Read endpoints are available to any signed-in user; the privileged actions (run a sweep,
review a change) require the admin token, reusing the existing X-Admin-Api-Token guard.
"""

from __future__ import annotations

import datetime as dt
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from agent.db.mongo import insert_audit_log
from agent.rules.loader import load_rulepack
from compliance.regwatch import collect_watch_sources, content_hash, detect_change
from compliance.registry import get_rulepack_ids
from saas.app.auth import get_current_user
from saas.app.database import get_collection, serialize_document
from saas.app.readiness import require_admin

router = APIRouter(prefix="/api/v1/regwatch", tags=["regwatch"])

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
Fetcher = Callable[[str], str]


def snapshots_collection():
    return get_collection("regulatory_snapshots")


def changes_collection():
    return get_collection("regulatory_changes")


def _load_all_packs() -> list[dict[str, Any]]:
    packs: list[dict[str, Any]] = []
    for pack_id in get_rulepack_ids():
        try:
            pack = load_rulepack(_PROJECT_ROOT / "rulepacks" / f"{pack_id}.yaml", validate=False)
            pack.setdefault("pack_id", pack_id)
            packs.append(pack)
        except Exception:
            continue
    return packs


def watch_sources() -> list[dict[str, Any]]:
    return collect_watch_sources(_load_all_packs())


def _default_fetcher(url: str) -> str:
    import requests  # lazy: optional at import time
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def run_watch_sweep(fetcher: Optional[Fetcher] = None, now: Optional[dt.datetime] = None) -> dict[str, Any]:
    """Fetch every watched source, snapshot it, and raise a pending change on any diff.

    Best-effort per source: a fetch failure is recorded and skipped, never aborts the sweep.
    Returns a summary including the changes created this run. Used by the cron entrypoint.
    """
    fetcher = fetcher or _default_fetcher
    now = now or dt.datetime.utcnow()
    snaps, changes = snapshots_collection(), changes_collection()

    created: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    checked = 0

    for source in watch_sources():
        url = source["url"]
        try:
            text = fetcher(url)
        except Exception as exc:
            errors.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
            continue
        checked += 1

        prev = snaps.find_one({"url": url}, sort=[("fetched_at", -1)])
        result = detect_change(prev.get("hash") if prev else None, text)
        snaps.insert_one({
            "url": url, "hash": result["new_hash"], "fetched_at": now,
            "rule_ids": source["rule_ids"], "pack_ids": source["pack_ids"],
        })

        if result["changed"]:
            # Dedup: skip if an open change for this url+new_hash already exists.
            if changes.find_one({"url": url, "new_hash": result["new_hash"], "status": "pending"}):
                continue
            change = {
                "change_id": f"chg_{uuid.uuid4().hex[:12]}",
                "url": url,
                "rule_ids": source["rule_ids"],
                "pack_ids": source["pack_ids"],
                "prev_hash": result["prev_hash"],
                "new_hash": result["new_hash"],
                "status": "pending",
                "detected_at": now,
                "note": "",
            }
            changes.insert_one(change)
            created.append(change)

    try:
        insert_audit_log({
            "source": "regwatch_sweep", "status": "completed", "timestamp": now,
            "metadata": {"checked": checked, "changes": len(created), "errors": len(errors)},
        })
    except Exception:
        pass

    return {"checked": checked, "changes_created": len(created),
            "changes": [serialize_document(c) for c in created], "errors": errors}


class ReviewRequest(BaseModel):
    decision: str = Field(description="approved | dismissed")
    note: str = Field(default="", max_length=2000)


@router.get("/sources")
async def list_sources(current_user: dict[str, Any] = Depends(get_current_user)):
    """The legal sources we watch and which rules cite each (signed-in)."""
    sources = watch_sources()
    return {"count": len(sources), "sources": sources}


@router.post("/run")
async def trigger_sweep(_admin: bool = Depends(require_admin)):
    """Run a watch sweep now (admin). The cron entrypoint calls run_watch_sweep directly."""
    return run_watch_sweep()


@router.get("/changes")
async def list_changes(status: str = "pending", current_user: dict[str, Any] = Depends(get_current_user)):
    """List detected regulatory changes (default: pending)."""
    query: dict[str, Any] = {}
    if status != "all":
        query["status"] = status
    docs = list(changes_collection().find(query).sort("detected_at", -1))
    return {"count": len(docs), "changes": [serialize_document(d) for d in docs]}


@router.post("/changes/{change_id}/review")
async def review_change(change_id: str, body: ReviewRequest, _admin: bool = Depends(require_admin)):
    """Human-gated decision on a change. Records the decision + note; NEVER edits a rulepack."""
    decision = body.decision.strip().lower()
    if decision not in {"approved", "dismissed"}:
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'dismissed'")
    change = changes_collection().find_one({"change_id": change_id})
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")

    now = dt.datetime.utcnow()
    changes_collection().update_one(
        {"change_id": change_id},
        {"$set": {"status": decision, "note": body.note, "reviewed_at": now}},
    )
    try:
        insert_audit_log({
            "source": "regwatch_review", "status": decision, "timestamp": now,
            "metadata": {"change_id": change_id, "url": change.get("url"),
                         "rule_ids": change.get("rule_ids", []), "note": body.note},
        })
    except Exception:
        pass
    # Approval is an acknowledgement that the cited rules need human re-verification against
    # LEGAL_REVIEW_NEEDED.md — it does not auto-modify rule content.
    return {"change_id": change_id, "status": decision,
            "rules_to_review": change.get("rule_ids", []) if decision == "approved" else []}
