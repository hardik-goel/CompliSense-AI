"""Tier-2 PII / data-flow inference API (Phase 4.3).

Exposes the names-only PII + data-flow engines (compliance/pii.py, compliance/dataflow.py)
to the product: a user supplies the NAMES of their data fields (optionally grouped into
sources with a provider/region), reviews inferred personal-data categories + data flows,
and confirms accepted suggestions into the project manifest — which the readiness wire
(Phase 3.4) then scores.

Guardrails: names only (never values); suggested-user-confirms (inference never writes the
manifest, ``/apply`` does, for accepted fields only); consent-gated persistence; full audit.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from agent.db.mongo import insert_audit_log
from compliance.dataflow import DataSource, infer_data_flows
from saas.app.auth import get_current_user
from saas.app.database import get_collection, serialize_document
from saas.app.projects import get_project_for_user, projects_collection

router = APIRouter(prefix="/projects", tags=["pii"])


def pii_collection():
    return get_collection("pii_inferences")


class PIISourceIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    field_names: list[str] = Field(default_factory=list)
    provider: str | None = None
    region: str | None = None


class InferRequest(BaseModel):
    sources: list[PIISourceIn] = Field(default_factory=list)
    field_names: list[str] = Field(default_factory=list)  # shorthand: ungrouped names
    consent_to_store: bool = False


class ApplyRequest(BaseModel):
    accepted_fields: list[str] = Field(default_factory=list)


def _merge_field(manifest: dict[str, Any], field: str, value: Any) -> None:
    existing = manifest.get(field)
    if isinstance(existing, list) and isinstance(value, list):
        manifest[field] = sorted(set(existing) | set(value))
    else:
        manifest[field] = value


@router.post("/{project_id}/pii/infer")
async def infer(
    project_id: str,
    body: InferRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Run names-only PII + data-flow inference; return the map + manifest suggestions."""
    get_project_for_user(project_id, current_user["id"])

    sources = [DataSource(name=s.name, field_names=s.field_names, provider=s.provider, region=s.region)
               for s in body.sources]
    if body.field_names:
        sources.append(DataSource(name="ungrouped", field_names=body.field_names))
    if not sources:
        raise HTTPException(status_code=400, detail="Provide sources or field_names")

    report = infer_data_flows(sources)

    inference_id = f"pii_{uuid.uuid4().hex[:12]}"
    now = dt.datetime.utcnow()
    stored = False
    if body.consent_to_store:
        pii_collection().insert_one({
            "inference_id": inference_id, "project_id": project_id, "user_id": current_user["id"],
            "created_at": now, "report": report, "applied_fields": [],
        })
        stored = True

    try:
        insert_audit_log({
            "user_id": current_user["id"], "project_id": project_id,
            "source": "pii_inference", "status": "completed", "timestamp": now,
            "metadata": {"sources": len(sources), "suggestions": len(report["suggestions"]),
                         "has_cross_border": report["has_cross_border"], "stored": stored},
        })
    except Exception:
        pass

    return {
        "inference_id": inference_id if stored else None,
        "stored": stored,
        "report": report,
        "disclaimer": "Inferred from field names only (never values). Suggestions are proposals — "
                      "review and confirm; nothing is applied automatically. Not legal advice.",
    }


@router.get("/{project_id}/pii/inferences")
async def list_inferences(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    get_project_for_user(project_id, current_user["id"])
    docs = list(pii_collection().find({"project_id": project_id}).sort("created_at", -1))
    out = []
    for d in docs:
        clean = serialize_document(d)
        report = clean.get("report", {})
        out.append({"inference_id": clean["inference_id"], "created_at": clean["created_at"],
                    "source_count": len(report.get("sources", [])),
                    "suggestion_count": len(report.get("suggestions", [])),
                    "has_cross_border": report.get("has_cross_border", False),
                    "applied_fields": clean.get("applied_fields", [])})
    return {"project_id": project_id, "count": len(out), "inferences": out}


@router.get("/{project_id}/pii/inferences/{inference_id}")
async def get_inference(project_id: str, inference_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    get_project_for_user(project_id, current_user["id"])
    doc = pii_collection().find_one({"inference_id": inference_id, "project_id": project_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Inference not found")
    return serialize_document(doc)


@router.post("/{project_id}/pii/inferences/{inference_id}/apply")
async def apply(
    project_id: str,
    inference_id: str,
    body: ApplyRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Confirm accepted suggestions into the project's discovered_manifest (read by readiness)."""
    get_project_for_user(project_id, current_user["id"])
    doc = pii_collection().find_one({"inference_id": inference_id, "project_id": project_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Inference not found")

    accepted = set(body.accepted_fields or [])
    by_field = {s["manifest_field"]: s["suggested_value"] for s in doc.get("report", {}).get("suggestions", [])}
    to_apply = {f: by_field[f] for f in accepted if f in by_field}
    if not to_apply:
        raise HTTPException(status_code=400, detail="No matching accepted suggestions to apply")

    project = projects_collection().find_one({"id": project_id})
    manifest = dict((project or {}).get("discovered_manifest") or {})
    for f, v in to_apply.items():
        _merge_field(manifest, f, v)

    now = dt.datetime.utcnow()
    projects_collection().update_one({"id": project_id}, {"$set": {"discovered_manifest": manifest, "updated_at": now}})
    pii_collection().update_one({"inference_id": inference_id},
                                {"$set": {"applied_fields": sorted(set(doc.get("applied_fields", [])) | set(to_apply))}})
    try:
        insert_audit_log({
            "user_id": current_user["id"], "project_id": project_id,
            "source": "pii_apply", "status": "applied", "timestamp": now,
            "metadata": {"inference_id": inference_id, "applied_fields": sorted(to_apply)},
        })
    except Exception:
        pass

    return {"project_id": project_id, "applied": sorted(to_apply), "discovered_manifest": manifest}
