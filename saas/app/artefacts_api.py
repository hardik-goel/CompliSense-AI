"""Artefact generator API (Tier-1.5).

For a client with gaps but no artefacts: list the artefacts that would close each gap and
**where each can be sourced from**, AI-draft them (consent-gated), let the client **explicitly
approve** each one, then download the approved set as a zip to drop into the scan input folder.

Guardrails kept throughout: drafts are stamped "DRAFT — REQUIRES LEGAL REVIEW"; nothing is
used until the client approves; the AI path is consent-gated and needs an Anthropic key; we are
honest about what we can/can't auto-fetch (only the Tier-1 connectors).
"""

from __future__ import annotations

import datetime as dt
import io
import zipfile
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from agent.db.mongo import insert_audit_log
from compliance.artefacts import (
    CONNECTABLE_SOURCES,
    GENERATED_ARTEFACTS,
    SOURCE_LABELS,
    needed_artefacts,
    spec_for,
)
from compliance.dfd import build_dfd, dfd_to_svg
from compliance.manifest import build_manifest
from compliance.ropa import ropa_to_markdown
from compliance.readiness import score_manifest
from saas.app.auth import get_current_user
from saas.app.copilot_api import _find_rule, get_copilot
from saas.app.database import get_collection, serialize_document
from saas.app.project_readiness import _PROJECT_PACKS
from saas.app.readiness import _load_pack
from saas.app.teams import get_project_with_role

router = APIRouter(prefix="/projects", tags=["artefacts"])
_DEFAULT_PACK = "dpdp_india_core_v1"


def artefacts_collection():
    return get_collection("generated_artefacts")


def _merged_answers(project: dict[str, Any]) -> dict[str, Any]:
    return {**(project.get("manifest_answers") or {}), **(project.get("discovered_manifest") or {})}


def _gap_rule_ids(project: dict[str, Any], pack_id: str) -> list[str]:
    report = score_manifest(build_manifest(_merged_answers(project)), _load_pack(pack_id))
    return [g.get("rule_id") for g in report.get("gaps", [])]


def _rule_dict(pack_id: str, rule_id: str) -> dict[str, Any]:
    raw = _find_rule(pack_id, rule_id)
    from agent.scoring.overall import readiness_framing
    return {"rule_id": raw.get("id"), "title": raw.get("title"),
            "rule_citation": raw.get("rule_citation"), "act_citation": raw.get("act_citation"),
            "clause": raw.get("clause"), "requirement": raw.get("description") or raw.get("requirement"),
            "framing": readiness_framing(raw.get("enforcement_date"), raw.get("date_status"))}


@router.get("/{project_id}/artefacts/needed")
async def list_needed(project_id: str, pack_id: str = _DEFAULT_PACK,
                      current_user: dict[str, Any] = Depends(get_current_user)):
    """Artefacts that would close this project's gaps + where each can be sourced from."""
    project, _role = get_project_with_role(project_id, current_user, "view")
    if pack_id not in _PROJECT_PACKS:
        pack_id = _DEFAULT_PACK
    needed = needed_artefacts(_gap_rule_ids(project, pack_id), project)
    existing = {a["art_id"]: a.get("status") for a in artefacts_collection().find({"project_id": project_id})}
    for n in needed:
        n["status"] = existing.get(n["artefact_id"], "needed")
    return {
        "project_id": project_id, "pack_id": pack_id, "count": len(needed), "artefacts": needed,
        "generated": [{**g, "endpoint": g["endpoint"].format(project_id=project_id)}
                      for g in GENERATED_ARTEFACTS],
        "sources_legend": SOURCE_LABELS,
        "we_can_connect_to": CONNECTABLE_SOURCES,
        "note": "We can auto-fetch facts only from the connectors above (read-only). Everything "
                "else comes from your questionnaire answers, an AI draft you approve, or material "
                "only you can provide. Drafts are not legal advice and require legal review.",
    }


@router.get("/{project_id}/artefacts/list")
async def list_artefacts(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    get_project_with_role(project_id, current_user, "view")
    docs = list(artefacts_collection().find({"project_id": project_id}))
    return {"project_id": project_id, "count": len(docs),
            "artefacts": [serialize_document(d) for d in docs]}


def _generated_files(project_id: str, project: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Deterministic artefacts built from confirmed facts — (filename, title, content).

    These are *generated*, not AI-drafted, so they need no approval step: a ROPA is a record
    of facts, and an LLM-written record would be a fabricated one. Best-effort — a failure
    here must never block the export of the approved drafts.
    """
    from saas.app.ropa_api import _build as _build_ropa
    try:
        ropa = _build_ropa(project_id, project)
    except Exception:
        return []
    return [
        ("record_of_processing.md", "Record of Processing Activities", ropa_to_markdown(ropa)),
        ("data_flow_diagram.svg", "Personal-data flow diagram", dfd_to_svg(build_dfd(ropa))),
    ]


@router.get("/{project_id}/artefacts/export.zip")
async def export_approved(project_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    """Download APPROVED artefacts as a zip to drop into the scan input folder."""
    project, _role = get_project_with_role(project_id, current_user, "view")
    approved = list(artefacts_collection().find({"project_id": project_id, "status": "approved"}))
    if not approved:
        raise HTTPException(status_code=404, detail="No approved artefacts yet — draft and approve some first.")

    generated = _generated_files(project_id, project)
    readme = (
        "CompliSense-AI — approved starter artefacts\n"
        "===========================================\n\n"
        "These are AI-DRAFTED, client-APPROVED starter documents. They are NOT legal advice and\n"
        "REQUIRE LEGAL REVIEW before you rely on them.\n\n"
        "HOW TO USE\n"
        "  Put this folder (or its files) into your scan input folder, then run the local agent:\n"
        "    python run_scan.py --project-path <this-folder> --output-dir ./output\n\n"
        "Files included:\n" + "\n".join(f"  - {a['filename']}  ({a['title']})" for a in approved) + "\n"
    )
    if generated:
        readme += (
            "\nGENERATED (not AI-drafted)\n"
            "  Built deterministically from your declared activities, data-flow inference and\n"
            "  questionnaire answers. Anything we could not source is stamped UNKNOWN rather than\n"
            "  guessed — see 'What is still missing' in the register.\n"
            + "\n".join(f"  - {name}  ({title})" for name, title, _ in generated) + "\n"
        )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("READ_ME_FIRST.txt", readme)
        for a in approved:
            z.writestr(a["filename"], a.get("content") or "")
        for name, _title, content in generated:
            z.writestr(name, content)
    buf.seek(0)
    _audit(current_user, project_id, "artefact_export", "exported",
           {"count": len(approved), "generated": [n for n, _, _ in generated]})
    return StreamingResponse(iter([buf.getvalue()]), media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="complisense_artefacts_{project_id}.zip"'})


@router.get("/{project_id}/artefacts/{art_id}")
async def get_artefact(project_id: str, art_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    get_project_with_role(project_id, current_user, "view")
    doc = artefacts_collection().find_one({"project_id": project_id, "art_id": art_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Artefact not generated yet")
    return serialize_document(doc)


@router.post("/{project_id}/artefacts/{art_id}/draft")
async def draft_artefact(project_id: str, art_id: str, consent_to_send: bool = False,
                         pack_id: str = _DEFAULT_PACK,
                         current_user: dict[str, Any] = Depends(get_current_user)):
    """AI-draft an artefact from the project's confirmed facts. Consent-gated; needs an LLM key."""
    project, _role = get_project_with_role(project_id, current_user, "use_copilot")
    if not consent_to_send:
        raise HTTPException(status_code=400, detail="consent_to_send is required: this sends the "
                            "cited rule + your confirmed, non-PII facts to the Anthropic API to draft the artefact.")
    spec = spec_for(art_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Unknown artefact id")
    if "ai_draft" not in spec["sources"]:
        raise HTTPException(status_code=400, detail="This artefact is manual — it cannot be AI-drafted.")
    if pack_id not in _PROJECT_PACKS:
        pack_id = _DEFAULT_PACK

    rule = _rule_dict(pack_id, spec["rule_id"])
    facts = _merged_answers(project)
    try:
        result = get_copilot().draft(rule, facts, spec["title"])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Drafting unavailable: {exc}") from exc

    now = dt.datetime.utcnow()
    doc = {"project_id": project_id, "art_id": art_id, "rule_id": spec["rule_id"],
           "title": spec["title"], "filename": spec["filename"], "status": "drafted",
           "content": result.get("answer", ""), "grounded": result.get("grounded"),
           "drafted_by": current_user["id"], "drafted_at": now, "approved_by": None, "approved_at": None}
    artefacts_collection().update_one({"project_id": project_id, "art_id": art_id}, {"$set": doc}, upsert=True)
    _audit(current_user, project_id, "artefact_draft", "drafted", {"art_id": art_id})
    return {"project_id": project_id, "art_id": art_id, "status": "drafted",
            "title": spec["title"], "filename": spec["filename"], "content": doc["content"],
            "disclaimer": result.get("disclaimer")}


@router.post("/{project_id}/artefacts/{art_id}/approve")
async def approve_artefact(project_id: str, art_id: str,
                           current_user: dict[str, Any] = Depends(get_current_user)):
    """Explicit client approval — only approved artefacts go into the export/input folder."""
    get_project_with_role(project_id, current_user, "edit_project")
    doc = artefacts_collection().find_one({"project_id": project_id, "art_id": art_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Artefact not generated yet")
    if doc.get("status") not in ("drafted", "approved"):
        raise HTTPException(status_code=400, detail="Only a drafted artefact can be approved")
    now = dt.datetime.utcnow()
    artefacts_collection().update_one({"project_id": project_id, "art_id": art_id},
        {"$set": {"status": "approved", "approved_by": current_user["id"], "approved_at": now}})
    _audit(current_user, project_id, "artefact_approve", "approved", {"art_id": art_id})
    return {"project_id": project_id, "art_id": art_id, "status": "approved"}


def _audit(user: dict[str, Any], project_id: str, source: str, status: str, meta: dict[str, Any]) -> None:
    try:
        insert_audit_log({"user_id": user["id"], "project_id": project_id, "source": source,
                          "status": status, "timestamp": dt.datetime.utcnow(), "metadata": meta})
    except Exception:
        pass
