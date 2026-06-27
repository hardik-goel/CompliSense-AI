"""LLM Remediation Copilot API (Phase 7).

Exposes the grounded copilot (compliance/copilot.py) to the product. For ONE rule, it sends
the cited rule + the project's confirmed, non-PII manifest facts to the model and returns an
explanation or a drafted remediation document.

Data path + consent (non-negotiable):
  - Runs ONLY with explicit ``consent_to_send`` — the user opts in to sending data to the LLM.
  - Sends only structured, non-PII facts: the rule text and the project's confirmed manifest
    booleans/categories (``discovered_manifest``). Never raw artefacts or personal-data values.
  - The exact facts sent are echoed back in ``data_sent`` for transparency.
  - Read-only and audited; the copilot drafts text, it never changes the user's systems.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from agent.db.mongo import insert_audit_log
from agent.rules.loader import iter_rules, load_rulepack
from agent.scoring.overall import readiness_framing
from compliance.copilot import RemediationCopilot, default_llm
from compliance.registry import get_rulepack_ids
from saas.app.auth import get_current_user
from saas.app.projects import get_project_for_user

router = APIRouter(prefix="/projects", tags=["copilot"])

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_VALID_MODES = {"explain", "draft"}


def get_copilot() -> RemediationCopilot:
    """Factory for the production copilot (Anthropic-backed). Patched in tests."""
    return RemediationCopilot(default_llm())


class RemediateRequest(BaseModel):
    rule_id: str = Field(min_length=1, max_length=120)
    pack_id: str = "dpdp_india_core_v1"
    mode: str = "explain"
    artifact_type: str | None = Field(default=None, max_length=120)
    consent_to_send: bool = False


def _find_rule(pack_id: str, rule_id: str) -> dict[str, Any]:
    if pack_id not in get_rulepack_ids():
        raise HTTPException(status_code=400, detail=f"Unknown pack_id. Available: {get_rulepack_ids()}")
    pack = load_rulepack(_PROJECT_ROOT / "rulepacks" / f"{pack_id}.yaml", validate=False)
    rule = next((r for r in iter_rules(pack) if r.get("id") == rule_id), None)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found in {pack_id}")
    return rule


@router.post("/{project_id}/copilot/remediate")
async def remediate(
    project_id: str,
    body: RemediateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    project = get_project_for_user(project_id, current_user["id"])

    if not body.consent_to_send:
        raise HTTPException(
            status_code=400,
            detail="consent_to_send is required: this sends the rule + your confirmed facts "
                   "(no raw artefacts or personal data) to the LLM.",
        )
    mode = body.mode.strip().lower()
    if mode not in _VALID_MODES:
        raise HTTPException(status_code=400, detail=f"mode must be one of {sorted(_VALID_MODES)}")

    raw = _find_rule(body.pack_id, body.rule_id)
    rule = {
        "rule_id": raw.get("id"),
        "title": raw.get("title"),
        "rule_citation": raw.get("rule_citation"),
        "act_citation": raw.get("act_citation"),
        "clause": raw.get("clause"),
        "requirement": raw.get("description") or raw.get("requirement"),
        "framing": readiness_framing(raw.get("enforcement_date"), raw.get("date_status")),
    }
    # Non-PII facts only: the project's confirmed manifest (booleans / categories).
    facts = dict(project.get("discovered_manifest") or {})

    copilot = get_copilot()
    try:
        if mode == "draft":
            result = copilot.draft(rule, facts, body.artifact_type or "remediation document")
        else:
            result = copilot.explain(rule, facts)
    except Exception as exc:  # LLM/SDK/network failure
        raise HTTPException(status_code=502, detail=f"Copilot unavailable: {exc}") from exc

    now = dt.datetime.utcnow()
    try:
        insert_audit_log({
            "user_id": current_user["id"], "project_id": project_id,
            "source": "copilot_remediate", "status": "completed", "timestamp": now,
            "metadata": {"rule_id": body.rule_id, "pack_id": body.pack_id, "mode": mode,
                         "grounded": result.get("grounded"), "fact_keys": sorted(facts.keys())},
        })
    except Exception:
        pass

    return {
        "project_id": project_id,
        "rule_id": body.rule_id,
        **result,
        "data_sent": {"rule_citation": rule["rule_citation"] or rule["act_citation"],
                      "fact_keys": sorted(facts.keys())},
    }
