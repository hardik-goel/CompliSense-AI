"""Record of Processing Activities (ROPA) + data-flow diagram API.

The register and the diagram are built **deterministically** from the project's confirmed
facts — declared processing activities first, then the latest names-only data-flow
inference, then the Tier-0 manifest. Nothing here is AI-drafted: a ROPA is a record, and a
fabricated record is worse than a missing one.

Anything we cannot source is stamped UNKNOWN and reported in ``unknowns`` with guidance,
so the client can see exactly what only they can supply. Both renders carry the
"DRAFT — requires legal review" framing used across the product.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field

from agent.db.mongo import insert_audit_log
from compliance.dfd import build_dfd, dfd_to_svg
from compliance.provenance import build_provenance
from compliance.ropa import ProcessingActivity, build_ropa, ropa_to_markdown
from saas.app.auth import get_current_user
from saas.app.database import get_collection
from saas.app.freshness_api import load_pack, provenance_collection
from saas.app.projects import projects_collection
from saas.app.teams import get_project_with_role

router = APIRouter(prefix="/projects", tags=["ropa"])

# The register cites rules that only exist in the extended pack (legitimate use, transfer,
# processor inventory), so provenance is stamped against that pack rather than core.
PROVENANCE_PACK = "dpdp_india_extended_v2"


def pii_collection():
    return get_collection("pii_inferences")


class ActivityIn(BaseModel):
    activity_id: str = Field(min_length=1, max_length=80)
    purpose: str | None = None
    categories: list[str] = Field(default_factory=list)
    data_principals: list[str] = Field(default_factory=list)
    stores: list[str] = Field(default_factory=list)
    retention: str | None = None
    legal_basis: str | None = None
    processors: list[str] = Field(default_factory=list)


class ActivitiesRequest(BaseModel):
    activities: list[ActivityIn] = Field(default_factory=list)


def _merged_answers(project: dict[str, Any]) -> dict[str, Any]:
    return {**(project.get("manifest_answers") or {}), **(project.get("discovered_manifest") or {})}


def _latest_flow_report(project_id: str) -> dict[str, Any] | None:
    """Most recent stored (consent-gated) PII/data-flow inference for this project."""
    docs = list(pii_collection().find({"project_id": project_id}))
    if not docs:
        return None
    latest = max(docs, key=lambda d: d.get("created_at") or 0)
    return latest.get("report")


def _activities(project: dict[str, Any]) -> list[ProcessingActivity] | None:
    raw = project.get("processing_activities") or []
    if not raw:
        return None
    return [ProcessingActivity(
        activity_id=a.get("activity_id") or "activity",
        purpose=a.get("purpose"),
        categories=list(a.get("categories") or []),
        data_principals=list(a.get("data_principals") or []),
        stores=list(a.get("stores") or []),
        retention=a.get("retention"),
        legal_basis=a.get("legal_basis"),
        processors=list(a.get("processors") or []),
    ) for a in raw]


def _build(project_id: str, project: dict[str, Any]) -> dict[str, Any]:
    ropa = build_ropa(
        _merged_answers(project),
        flow_report=_latest_flow_report(project_id),
        activities=_activities(project),
        generated_at=dt.datetime.utcnow().isoformat() + "Z",
    )
    # Stamp what this register was built from, so staleness is computable later rather than
    # guessed. A failure to load the pack must not break generation — it degrades to an
    # unstamped artefact, which the freshness report then reports as unverifiable.
    try:
        ropa["provenance"] = build_provenance(
            load_pack(PROVENANCE_PACK),
            ropa.get("supports_rules") or [],
            domains=(ropa.get("domains") or {}).get("applicable") or [],
        )
    except Exception:
        ropa["provenance"] = None
    return ropa


def _record_provenance(project_id: str, artefact_id: str, ropa: dict[str, Any]) -> None:
    """Remember the stamp of what we just handed the client, keyed by artefact."""
    stamp = ropa.get("provenance")
    if not stamp:
        return
    provenance_collection().update_one(
        {"project_id": project_id, "artefact_id": artefact_id},
        {"$set": {"provenance": stamp, "generated_at": ropa.get("generated_at")}},
        upsert=True,
    )


@router.get("/{project_id}/ropa")
async def get_ropa(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    """The Record of Processing Activities register, with completeness and open unknowns."""
    project, _role = get_project_with_role(project_id, current_user, "view")
    ropa = _build(project_id, project)
    return {
        "project_id": project_id,
        "ropa": ropa,
        "note": "Built deterministically from your declared activities, data-flow inference and "
                "questionnaire answers — never AI-drafted. Fields we cannot source are marked "
                "UNKNOWN rather than guessed.",
    }


@router.put("/{project_id}/ropa/activities")
async def save_activities(project_id: str, body: ActivitiesRequest,
                          current_user: dict[str, Any] = Depends(get_current_user)):
    """Declare processing activities — the only way the register reaches 100% complete."""
    get_project_with_role(project_id, current_user, "edit_project")
    activities = [a.model_dump() for a in body.activities]
    now = dt.datetime.utcnow()
    projects_collection().update_one(
        {"id": project_id},
        {"$set": {"processing_activities": activities, "updated_at": now}},
    )
    _audit(current_user, project_id, "ropa_activities", "saved", {"count": len(activities)})
    return {"project_id": project_id, "count": len(activities), "activities": activities}


@router.get("/{project_id}/ropa.md")
async def get_ropa_markdown(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    """The register as a Markdown artefact (drop into the scan input folder / evidence pack)."""
    project, _role = get_project_with_role(project_id, current_user, "view")
    ropa = _build(project_id, project)
    markdown = ropa_to_markdown(ropa)
    _record_provenance(project_id, "record_of_processing", ropa)
    _audit(current_user, project_id, "ropa_export", "exported", {"format": "markdown"})
    return Response(content=markdown, media_type="text/markdown", headers={
        "Content-Disposition": f'attachment; filename="record_of_processing_{project_id}.md"'})


@router.get("/{project_id}/ropa/dfd.svg")
async def get_dfd_svg(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    """The personal-data flow diagram for the same register. Self-contained SVG."""
    project, _role = get_project_with_role(project_id, current_user, "view")
    ropa = _build(project_id, project)
    svg = dfd_to_svg(build_dfd(ropa))
    _record_provenance(project_id, "data_flow_diagram", ropa)
    _audit(current_user, project_id, "ropa_export", "exported", {"format": "dfd_svg"})
    return Response(content=svg, media_type="image/svg+xml")


def _audit(user: dict[str, Any], project_id: str, source: str, status: str,
           meta: dict[str, Any]) -> None:
    try:
        insert_audit_log({"user_id": user["id"], "project_id": project_id, "source": source,
                          "status": status, "timestamp": dt.datetime.utcnow(), "metadata": meta})
    except Exception:
        pass
