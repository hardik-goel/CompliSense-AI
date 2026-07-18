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
from compliance.regwatch import (
    build_change_proposal,
    collect_watch_sources,
    content_hash,
    detect_change,
    merge_watch_sources,
    normalize_text,
)
from compliance.registry import get_rulepack_ids
from saas.app.auth import get_current_user
from saas.app.database import get_collection, serialize_document
from saas.app.readiness import require_admin

router = APIRouter(prefix="/api/v1/regwatch", tags=["regwatch"])

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Approved proposals are written here as git-friendly YAML patch STUBS for a human to apply
# by hand. The engine never applies them itself.
_PROPOSALS_DIR = _PROJECT_ROOT / "rulepacks" / "proposals"
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


def _all_rules() -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for pack in _load_all_packs():
        rules.extend(pack.get("rules", []) or [])
    return rules


def watch_sources() -> list[dict[str, Any]]:
    """Watched sources = rulepack-cited URLs unioned with the seed watchlist."""
    return merge_watch_sources(collect_watch_sources(_load_all_packs()))


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
            "rule_ids": source.get("rule_ids", []), "pack_ids": source.get("pack_ids", []),
            # Store the normalized text so the NEXT sweep can build a real diff summary.
            "text": normalize_text(text),
        })

        if result["changed"]:
            # Dedup: skip if an open change for this url+new_hash already exists.
            if changes.find_one({"url": url, "new_hash": result["new_hash"], "status": "pending"}):
                continue
            # Build a human-review-ONLY change proposal (diff, affected rules, action hint).
            proposal = build_change_proposal(
                source=source,
                prev_text=(prev or {}).get("text", "") if prev else "",
                new_text=text,
                all_rules=_all_rules(),
            )
            change = {
                "change_id": f"chg_{uuid.uuid4().hex[:12]}",
                "url": url,
                "rule_ids": source.get("rule_ids", []),
                "pack_ids": source.get("pack_ids", []),
                "prev_hash": result["prev_hash"],
                "new_hash": result["new_hash"],
                "status": "pending",
                "detected_at": now,
                "note": "",
                "proposal": proposal,
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


# ── Change-proposal pipeline (Phase 5.4) ─────────────────────────────────────
# A detected change carries an embedded `proposal` (built in run_watch_sweep). These
# endpoints let a human list proposals and approve/reject them. Approval writes a
# git-friendly YAML patch STUB under rulepacks/proposals/ for a human to apply by hand —
# it NEVER edits a live rulepack.


class ProposalReview(BaseModel):
    decision: str = Field(description="approved | rejected")
    note: str = Field(default="", max_length=2000)


def _write_proposal_patch(change: dict[str, Any], now: dt.datetime) -> Path:
    """Write an approved proposal as a YAML patch stub. Returns the file path.

    The stub is a human-editable scaffold: it records the source, affected rules, proposed
    action, and diff summary, with placeholder fields for the reviewer to fill. Applying it
    to a rulepack is a manual, reviewed step — never automatic.
    """
    import yaml  # lazy: keep module import light

    _PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    change_id = change.get("change_id", "unknown")
    proposal = change.get("proposal") or {}
    patch = {
        "proposal_id": change_id,
        "status": "approved_pending_manual_apply",
        "generated_at": now.isoformat(),
        "auto_applied": False,
        "source": proposal.get("source", {"url": change.get("url")}),
        "affected_rule_ids": proposal.get("affected_rule_ids", change.get("rule_ids", [])),
        "proposed_action": proposal.get("proposed_action", "review_only"),
        "diff_summary": proposal.get("diff_summary", {}),
        "reviewer_note": change.get("review_note", ""),
        "manual_edit_required": (
            "Fill in the concrete rulepack edit below, then apply by hand. This file does "
            "NOT modify any rulepack on its own."
        ),
        "suggested_edit": {
            "pack_id": None,
            "rule_id": None,
            "field": None,        # e.g. enforcement_date / new rule
            "current_value": None,
            "proposed_value": None,
        },
    }
    path = _PROPOSALS_DIR / f"{change_id}.yaml"
    path.write_text(yaml.safe_dump(patch, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


@router.get("/proposals")
async def list_proposals(status: str = "pending", current_user: dict[str, Any] = Depends(get_current_user)):
    """List change proposals (changes that carry an embedded proposal). Default: pending."""
    docs = list(changes_collection().find({}).sort("detected_at", -1))
    out = []
    for d in docs:
        if not d.get("proposal"):
            continue
        if status != "all" and d.get("status") != status:
            continue
        out.append({
            "change_id": d.get("change_id"),
            "url": d.get("url"),
            "status": d.get("status"),
            "detected_at": d.get("detected_at"),
            "proposal": d.get("proposal"),
            "proposal_patch_path": d.get("proposal_patch_path"),
        })
    return {"count": len(out), "proposals": [serialize_document(p) for p in out]}


@router.post("/proposals/{change_id}/review")
async def review_proposal(change_id: str, body: ProposalReview, _admin: bool = Depends(require_admin)):
    """Human-gated proposal decision. approve → writes a YAML patch stub; reject → archived.

    NEVER edits a live rulepack. Approval only scaffolds a patch file for manual application.
    """
    decision = body.decision.strip().lower()
    if decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'rejected'")
    change = changes_collection().find_one({"change_id": change_id})
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    if not change.get("proposal"):
        raise HTTPException(status_code=400, detail="Change has no proposal to review")

    now = dt.datetime.utcnow()
    update: dict[str, Any] = {"status": decision, "review_note": body.note, "reviewed_at": now}
    patch_path: str | None = None
    if decision == "approved":
        try:
            path = _write_proposal_patch({**change, "review_note": body.note}, now)
            try:
                patch_path = str(path.relative_to(_PROJECT_ROOT))
            except ValueError:  # patch dir outside the repo (e.g. tests) — use absolute
                patch_path = str(path)
        except Exception as exc:  # never 500 the review because file IO hiccupped
            raise HTTPException(status_code=500, detail=f"Could not write patch: {exc}")
        update["proposal_patch_path"] = patch_path
    changes_collection().update_one({"change_id": change_id}, {"$set": update})

    try:
        insert_audit_log({
            "source": "regwatch_proposal_review", "status": decision, "timestamp": now,
            "metadata": {"change_id": change_id, "url": change.get("url"),
                         "patch_path": patch_path, "note": body.note},
        })
    except Exception:
        pass
    return {
        "change_id": change_id,
        "status": decision,
        "proposal_patch_path": patch_path,
        "rules_to_review": change.get("proposal", {}).get("affected_rule_ids", []) if decision == "approved" else [],
    }
