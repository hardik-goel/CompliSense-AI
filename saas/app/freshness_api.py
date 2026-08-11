"""Artefact freshness — "is the document my client is holding still current law?"

The regulatory watcher (``compliance/regwatch.py``) tells us when a *legal source* moved.
The provenance stamp (``compliance/provenance.py``) tells us what each generated artefact was
*built from*. This module is the join between them, and it is the thing that makes a
generated compliance document trustworthy over time rather than only on the day it was made.

Two reads:
  ``GET /projects/{id}/artefacts/freshness``     every artefact this project exported, with
                                                fresh / review / stale and why.
  ``GET /projects/{id}/artefacts/change-impact`` given the rule IDs a regwatch proposal
                                                flagged, which of this client's artefacts
                                                that invalidates.

Neither endpoint mutates an artefact. Regeneration stays an explicit act by the client, for
the same reason the watcher never edits a rulepack: a system that silently rewrites the
client's compliance evidence is one nobody can audit.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from agent.db.mongo import insert_audit_log
from agent.rules.loader import load_rulepack
from compliance.provenance import assess_freshness, impacted_artefacts
from saas.app.auth import get_current_user
from saas.app.database import get_collection
from saas.app.teams import get_project_with_role

router = APIRouter(prefix="/projects", tags=["freshness"])

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Human labels for the artefacts we stamp, so a freshness report reads like a document list.
_TITLES = {
    "record_of_processing": "Record of Processing Activities (ROPA)",
    "data_flow_diagram": "Personal-data flow diagram (DFD)",
}


def provenance_collection():
    return get_collection("artefact_provenance")


def changes_collection():
    return get_collection("regwatch_changes")


def load_pack(pack_id: str) -> dict[str, Any]:
    """Load a rulepack by id. Public because ropa_api stamps provenance against it too."""
    return load_rulepack(_PROJECT_ROOT / "rulepacks" / f"{pack_id}.yaml", validate=False)


def _stamped(project_id: str) -> list[dict[str, Any]]:
    return list(provenance_collection().find({"project_id": project_id}))


@router.get("/{project_id}/artefacts/freshness")
async def get_freshness(project_id: str,
                        current_user: dict[str, Any] = Depends(get_current_user)):
    """Re-check every exported artefact against the rulepack as it stands today."""
    get_project_with_role(project_id, current_user, "view")

    out: list[dict[str, Any]] = []
    packs: dict[str, dict[str, Any]] = {}
    for doc in _stamped(project_id):
        stamp = doc.get("provenance") or {}
        pack_id = stamp.get("pack_id")
        if pack_id and pack_id not in packs:
            try:
                packs[pack_id] = load_pack(pack_id)
            except Exception:
                packs[pack_id] = {}
        result = assess_freshness(stamp, packs.get(pack_id) or {})
        out.append({
            "artefact_id": doc.get("artefact_id"),
            "title": _TITLES.get(doc.get("artefact_id"), doc.get("artefact_id")),
            "generated_at": doc.get("generated_at"),
            "pack_id": pack_id,
            "built_against_version": stamp.get("pack_version"),
            "current_version": result.get("pack_version"),
            "status": result["status"],
            "reasons": result["reasons"],
            "regenerate": result["status"] == "stale",
        })

    out.sort(key=lambda a: (a["status"] != "stale", a["artefact_id"]))
    counts = {s: sum(1 for a in out if a["status"] == s) for s in ("fresh", "review", "stale")}
    return {
        "project_id": project_id,
        "artefacts": out,
        "summary": {**counts, "total": len(out)},
        "note": "Freshness compares each artefact against the rulepack version it was built "
                "from. Nothing is regenerated automatically — re-generating is your call, so "
                "the change is on the record.",
    }


@router.get("/{project_id}/artefacts/change-impact")
async def get_change_impact(project_id: str, rule_ids: str = "",
                            current_user: dict[str, Any] = Depends(get_current_user)):
    """Given the rules a regulatory change touched, which of this client's artefacts it hits."""
    get_project_with_role(project_id, current_user, "view")
    wanted = [r.strip() for r in (rule_ids or "").split(",") if r.strip()]
    if not wanted:
        raise HTTPException(status_code=400,
                            detail="Provide rule_ids (comma-separated) from the regwatch change.")

    artefacts = [{"artefact_id": d.get("artefact_id"), "provenance": d.get("provenance")}
                 for d in _stamped(project_id)]
    hits = impacted_artefacts(wanted, artefacts)
    for h in hits:
        h["title"] = _TITLES.get(h["artefact_id"], h["artefact_id"])

    _audit(current_user, project_id, "artefact_change_impact", "checked",
           {"rule_ids": wanted, "impacted": [h["artefact_id"] for h in hits]})
    return {
        "project_id": project_id,
        "rule_ids": wanted,
        "impacted": hits,
        "note": "An artefact is impacted either because it was built from a changed rule, or "
                "because it claims to cover a DPDPA domain that rule belongs to.",
    }


@router.get("/{project_id}/artefacts/regwatch-impact")
async def get_regwatch_impact(project_id: str,
                              current_user: dict[str, Any] = Depends(get_current_user)):
    """Early warning: a watched legal source moved, but no rule has been edited yet.

    ``/freshness`` can only see changes that already landed in a rulepack — which happens
    after a human reviews the proposal. This closes the gap in between, so a client is not
    the last to know that the ground under their documents is shifting.
    """
    get_project_with_role(project_id, current_user, "view")

    artefacts = [{"artefact_id": d.get("artefact_id"), "provenance": d.get("provenance")}
                 for d in _stamped(project_id)]
    pending = [d for d in changes_collection().find({})
               if d.get("proposal") and d.get("status") == "pending"]

    warnings: list[dict[str, Any]] = []
    for change in pending:
        proposal = change.get("proposal") or {}
        hits = impacted_artefacts(proposal.get("affected_rule_ids") or [], artefacts)
        if not hits:
            continue
        for h in hits:
            h["title"] = _TITLES.get(h["artefact_id"], h["artefact_id"])
        warnings.append({
            "change_id": change.get("change_id"),
            "source": proposal.get("source") or {"url": change.get("url")},
            "detected_at": change.get("detected_at"),
            "affected_rule_ids": proposal.get("affected_rule_ids") or [],
            "proposed_action": proposal.get("proposed_action"),
            "impacted": hits,
        })

    return {
        "project_id": project_id,
        "pending_changes": len(pending),
        "warnings": warnings,
        "note": "These are DETECTED source changes awaiting human review — no rule has been "
                "changed and nothing has been applied to your rulepack or your documents. "
                "Treat them as an early heads-up, not a finding.",
    }


def _audit(user: dict[str, Any], project_id: str, source: str, status: str,
           meta: dict[str, Any]) -> None:
    try:
        import datetime as dt
        insert_audit_log({"user_id": user["id"], "project_id": project_id, "source": source,
                          "status": status, "timestamp": dt.datetime.utcnow(), "metadata": meta})
    except Exception:
        pass
