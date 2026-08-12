"""Project readiness from the discovered manifest (Phase 3 → readiness wire).

Closes the loop: connector discovery → confirmed `discovered_manifest` → applicability-gated
readiness scoring. A project's readiness is scored over the merge of any self-declared
questionnaire answers (`manifest_answers`) with the connector-confirmed `discovered_manifest`
(discovery wins, since it is evidence from the live account). Controls that a connector
corroborated are tagged so the UI can show "auto-filled from <provider>".

Read-only, readiness framing, not legal advice — same guarantees as the Phase 1 tool.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from compliance.domains import domain_rollup
from compliance.manifest import build_manifest, manifest_to_profile
from compliance.readiness import score_manifest
from saas.app.auth import get_current_user
from saas.app.projects import get_project_for_user
from saas.app.readiness import _ALLOWED_PACKS, _load_pack

router = APIRouter(prefix="/projects", tags=["readiness"])

# Project readiness scores DPDP and (role-gated) EU AI Act packs. The public DPDP tool
# (saas/app/readiness.py) stays DPDP-only; EU rules are pending legal review.
_PROJECT_PACKS = set(_ALLOWED_PACKS) | {"euai_core_v1", "euai_extended_v1"}

# Readiness rules a Tier-1 connector can corroborate -> the manifest field it sets.
_CONNECTOR_BACKED_RULES: Dict[str, str] = {
    "DPDP-SEC8-OBLIGATIONS-001": "has_security_safeguards",
    "DPDP-SEC8-OBLIGATIONS-003": "retention_defined",
}


def _merged_answers(project: Dict[str, Any]) -> Dict[str, Any]:
    """Self-declared answers overlaid by connector-confirmed facts (discovery wins)."""
    base = dict(project.get("manifest_answers") or {})
    base.update(project.get("discovered_manifest") or {})
    return base


@router.get("/{project_id}/readiness")
async def project_readiness(
    project_id: str,
    pack_id: str = "dpdp_india_core_v1",
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Score the project's merged manifest and tag controls backed by connector evidence."""
    project = get_project_for_user(project_id, current_user["id"])
    if pack_id not in _PROJECT_PACKS:
        raise HTTPException(status_code=400, detail=f"Unsupported pack_id: {pack_id}")

    discovered = project.get("discovered_manifest") or {}
    answers = _merged_answers(project)
    manifest = build_manifest(answers)
    report = score_manifest(manifest, _load_pack(pack_id))

    # Tag any ready/gap item that a connector corroborated, so the UI can attribute it.
    for item in report.get("ready", []) + report.get("gaps", []):
        field = _CONNECTOR_BACKED_RULES.get(item.get("rule_id"))
        if field and field in discovered:
            item["evidence_source"] = "connector"

    # The engine scores rule by rule; the market reads domain by domain. Same findings,
    # re-cut through the eight-domain lens (empty for non-DPDP packs, by design).
    report["domains"] = domain_rollup(report)

    report["evidence"] = {
        "discovered_fields": sorted(discovered.keys()),
        "has_discovery": bool(discovered),
        "profile": manifest_to_profile(manifest),
    }
    return report
