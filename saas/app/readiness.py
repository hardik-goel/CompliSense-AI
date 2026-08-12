"""
Public DPDP Readiness Score API (Phase 1.3).

A no-login lead magnet: a visitor answers the Tier-0 questionnaire and gets a readiness
score + a teaser of the top 3 gaps. The full gap list + remediation is gated behind signup
(returned only to authenticated users). Honest lead magnet — no fabricated data.

Privacy ("without storing your data"): anonymous submissions are EPHEMERAL — this module
does not persist anything. Persistence for signed-in users is added in Phase 1.5.
"""

from __future__ import annotations

import datetime as dt
import logging
import secrets
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from agent.rules.loader import load_rulepack
from compliance.manifest import build_manifest, get_questionnaire, validate_answers
from compliance.readiness import score_manifest, top_gaps
from saas.app.analytics import record_event, score_bucket
from saas.app.auth import get_current_user, get_current_user_optional
from saas.app.config import settings
from saas.app.database import get_collection, serialize_document


async def require_admin(
    x_admin_api_token: Optional[str] = Header(default=None, alias="X-Admin-Api-Token"),
) -> bool:
    """Admin-only guard: requires the X-Admin-Api-Token header to match the configured token."""
    if not x_admin_api_token or not secrets.compare_digest(x_admin_api_token, settings.admin_api_token):
        raise HTTPException(status_code=403, detail="Admin token required")
    return True

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/readiness", tags=["readiness"])

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
# DPDP packs are fully scored; EU AI Act packs are role-gated and surface obligations only
# (no numeric score until EU posture scoring is built + legally reviewed).
_DPDP_PACKS = {"dpdp_india_core_v1", "dpdp_india_extended_v1", "dpdp_india_extended_v2"}
_ALLOWED_PACKS = _DPDP_PACKS | {
    "euai_core_v1", "euai_extended_v1", "euai_core_v2", "euai_extended_v2"
}


def assessments_collection():
    return get_collection("readiness_assessments")


@lru_cache(maxsize=4)
def _load_pack(pack_id: str) -> Dict[str, Any]:
    path = _PROJECT_ROOT / "rulepacks" / f"{pack_id}.yaml"
    return load_rulepack(path, validate=False)


class ScoreRequest(BaseModel):
    answers: Dict[str, Any]
    pack_id: str = "dpdp_india_core_v1"
    consent_to_store: bool = False  # only meaningful for signed-in users (Phase 1.5)


@router.get("/questionnaire")
async def get_questionnaire_endpoint():
    """Return the questionnaire definition for the public tool to render."""
    return {"questions": get_questionnaire()}


@router.post("/score")
async def score_endpoint(
    payload: ScoreRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """Score answers. Anonymous → score + top-3 teaser. Signed-in → full report.

    Anonymous answers are not stored (ephemeral). Nothing is written here in Phase 1.3.
    """
    if payload.pack_id not in _ALLOWED_PACKS:
        raise HTTPException(status_code=400, detail=f"Unsupported pack_id: {payload.pack_id}")

    missing = validate_answers(payload.answers)
    manifest = build_manifest(payload.answers)
    pack = _load_pack(payload.pack_id)
    report = score_manifest(manifest, pack)

    # First-party, non-PII funnel event (no answers/email stored).
    record_event("readiness_completed", {
        "authenticated": bool(user),
        "score_bucket": score_bucket(report["readiness_score"]) if report["readiness_score"] is not None else "na",
        "pack_id": payload.pack_id,
        "jurisdiction": report["jurisdiction"],
        "complete": not missing,
    })

    response: Dict[str, Any] = {
        "readiness_score": report["readiness_score"],
        "scoring_available": report.get("scoring_available", True),
        "obligations_identified": report.get("obligations_identified", 0),
        "summary": report["summary"],
        "jurisdiction": report["jurisdiction"],
        "pack_id": report["pack_id"],
        "pack_version": report.get("pack_version"),
        "rules_current_as_of": report.get("rules_current_as_of"),
        "scope_exclusions": report.get("scope_exclusions", []),
        "authenticated": bool(user),
        "incomplete_questions": missing,
        "disclaimer": report["disclaimer"],
    }

    if user:
        # Full report for signed-in users.
        response["gaps"] = report["gaps"]
        response["ready"] = report["ready"]
        response["not_applicable"] = report["not_applicable"]
        response["full_report"] = True

        # Persist ONLY for signed-in users who explicitly consent. Anonymous = ephemeral.
        response["saved"] = False
        if payload.consent_to_store:
            try:
                doc = {
                    "id": str(uuid.uuid4()),
                    "user_id": user["id"],
                    "created_at": dt.datetime.utcnow(),
                    "pack_id": payload.pack_id,
                    "answers": payload.answers,
                    "readiness_score": report["readiness_score"],
                    "summary": report["summary"],
                }
                assessments_collection().insert_one(doc)
                response["saved"] = True
                response["assessment_id"] = doc["id"]
            except Exception as e:  # never fail the score because storage hiccupped
                logger.warning("Could not persist assessment: %s", e)
    else:
        # Honest teaser: show the top 3 gaps + how many more are gated behind signup.
        response["top_gaps"] = top_gaps(report, 3)
        response["gaps_locked"] = max(0, report["summary"]["gaps"] - 3)
        response["full_report"] = False
        response["signup_required_for_full_report"] = True

    return response


@router.get("/analytics/summary")
async def analytics_summary(_admin: bool = Depends(require_admin)):
    """Funnel counts (ADMIN only, via X-Admin-Api-Token). Aggregate, non-PII."""
    from saas.app.analytics import funnel_summary
    return {"funnel": funnel_summary()}


@router.get("/assessments")
async def list_assessments(user: dict = Depends(get_current_user)):
    """List the signed-in user's saved assessments (most recent first)."""
    docs = list(
        assessments_collection()
        .find({"user_id": user["id"]})
        .sort("created_at", -1)
    )
    return {"assessments": [serialize_document(d) for d in docs]}


@router.get("/assessments/{assessment_id}")
async def get_assessment(assessment_id: str, user: dict = Depends(get_current_user)):
    """Fetch one saved assessment and re-derive its full report from stored answers."""
    doc = assessments_collection().find_one({"id": assessment_id, "user_id": user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Assessment not found")
    manifest = build_manifest(doc.get("answers", {}))
    report = score_manifest(manifest, _load_pack(doc.get("pack_id", "dpdp_india_core_v1")))
    return {"assessment": serialize_document(doc), "report": report}
