"""CompliSense MCP tools — pure registry + handlers (Phase 6.1).

Each tool is a name + JSON-Schema input + a handler(args) -> JSON-serializable dict. Handlers
reuse the existing compliance/connectors engine and do NO I/O (no DB, no network, no creds),
so the MCP server runs standalone and these are trivially unit-testable without the `mcp` SDK.

Read-only and readiness-framed throughout; never a legal determination.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List

from agent.rules.loader import iter_rules, load_rulepack
from agent.scoring.overall import readiness_framing
from compliance.dataflow import DataSource, infer_data_flows
from compliance.manifest import build_manifest, get_questionnaire
from compliance.pii import infer_pii, pii_to_suggestion
from compliance.readiness import score_manifest
from compliance.registry import get_rulepack_catalog, get_rulepack_ids
from connectors.registry import CONNECTOR_REQUIREMENTS, available_providers, get_connector

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Readiness scoring: DPDP (full predicate coverage) + EU AI Act (role-gated; EU posture
# items surface as needs-review, and EU rules are pending legal review).
_SCORE_PACKS = {"dpdp_india_core_v1", "dpdp_india_extended_v1", "euai_core_v1", "euai_extended_v1"}
_NOT_LEGAL_ADVICE = "Readiness signal, not legal advice or a determination of compliance."


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]


def _load_pack(pack_id: str) -> Dict[str, Any]:
    return load_rulepack(_PROJECT_ROOT / "rulepacks" / f"{pack_id}.yaml", validate=False)


# ── handlers ─────────────────────────────────────────────────────────────────

def _list_rulepacks(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"rulepacks": get_rulepack_catalog()}


def _list_rules(args: Dict[str, Any]) -> Dict[str, Any]:
    pack_id = args.get("pack_id")
    if pack_id not in get_rulepack_ids():
        raise ValueError(f"Unknown pack_id. Available: {get_rulepack_ids()}")
    rules = []
    for r in iter_rules(_load_pack(pack_id)):
        rules.append({
            "rule_id": r.get("id"), "title": r.get("title"), "clause": r.get("clause"),
            "severity": r.get("severity"), "act_citation": r.get("act_citation"),
            "rule_citation": r.get("rule_citation"), "source_url": r.get("source_url"),
            "enforcement_date": r.get("enforcement_date"), "date_status": r.get("date_status"),
            "verification": r.get("verification"),
            "framing": readiness_framing(r.get("enforcement_date"), r.get("date_status")),
        })
    return {"pack_id": pack_id, "count": len(rules), "rules": rules}


def _get_questionnaire(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"questions": get_questionnaire()}


def _score_readiness(args: Dict[str, Any]) -> Dict[str, Any]:
    pack_id = args.get("pack_id", "dpdp_india_core_v1")
    if pack_id not in _SCORE_PACKS:
        raise ValueError(f"Readiness scoring supports DPDP packs only: {sorted(_SCORE_PACKS)}")
    answers = args.get("answers") or {}
    if not isinstance(answers, dict):
        raise ValueError("answers must be an object of questionnaire answers")
    report = score_manifest(build_manifest(answers), _load_pack(pack_id))
    return report  # already carries its own readiness disclaimer


def _infer_pii(args: Dict[str, Any]) -> Dict[str, Any]:
    field_names = args.get("field_names") or []
    if not isinstance(field_names, list):
        raise ValueError("field_names must be a list of strings (names only, never values)")
    findings = infer_pii(field_names)
    sug = pii_to_suggestion(findings)
    return {
        "findings": [f.to_dict() for f in findings],
        "suggestion": sug.to_dict() if sug else None,
        "note": "Inferred from field NAMES only (never values). " + _NOT_LEGAL_ADVICE,
    }


def _infer_data_flows(args: Dict[str, Any]) -> Dict[str, Any]:
    raw = args.get("sources") or []
    if not isinstance(raw, list) or not raw:
        raise ValueError("sources must be a non-empty list of {name, field_names, provider?, region?}")
    sources = [DataSource(name=s.get("name", "source"), field_names=s.get("field_names", []),
                          provider=s.get("provider"), region=s.get("region")) for s in raw]
    report = infer_data_flows(sources)
    report["note"] = "Inferred from field NAMES only. " + _NOT_LEGAL_ADVICE
    return report


def _list_connectors(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"providers": available_providers(), "requirements": CONNECTOR_REQUIREMENTS}


def _connector_policy(args: Dict[str, Any]) -> Dict[str, Any]:
    provider = args.get("provider")
    if provider not in available_providers():
        raise ValueError(f"Unknown provider. Available: {available_providers()}")
    placeholders = {
        "aws": {"role_arn": "arn:aws:iam::ACCOUNT_ID:role/CompliSenseReadOnly"},
        "gcp": {"project_id": "YOUR_PROJECT_ID"}, "azure": {"subscription_id": "YOUR_SUBSCRIPTION_ID"},
        "github": {"org": "YOUR_ORG"},
    }
    conn = get_connector(provider, **placeholders.get(provider, {}))
    return {"provider": provider, "requirements": CONNECTOR_REQUIREMENTS.get(provider, []),
            "least_privilege_policy": conn.least_privilege_policy()}


# ── registry ─────────────────────────────────────────────────────────────────

TOOLS: List[Tool] = [
    Tool("list_rulepacks", "List available CompliSense rulepacks (DPDP India, EU AI Act).",
         {"type": "object", "properties": {}}, _list_rulepacks),
    Tool("list_rules", "List a rulepack's rules with dual citations, enforcement dates, and readiness framing.",
         {"type": "object", "properties": {"pack_id": {"type": "string"}}, "required": ["pack_id"]}, _list_rules),
    Tool("get_questionnaire", "Get the Tier-0 readiness questionnaire (manifest questions).",
         {"type": "object", "properties": {}}, _get_questionnaire),
    Tool("score_readiness",
         "Score Tier-0 DPDP readiness from questionnaire answers. Applicability-gated; unknown counts as a gap.",
         {"type": "object", "properties": {
             "answers": {"type": "object", "description": "questionnaire answers"},
             "pack_id": {"type": "string", "default": "dpdp_india_core_v1"}}, "required": ["answers"]},
         _score_readiness),
    Tool("infer_pii",
         "Infer personal-data categories from field/column NAMES (never values).",
         {"type": "object", "properties": {
             "field_names": {"type": "array", "items": {"type": "string"}}}, "required": ["field_names"]},
         _infer_pii),
    Tool("infer_data_flows",
         "Infer where PII categories live across data sources + cross-border flags, from field NAMES only.",
         {"type": "object", "properties": {"sources": {"type": "array", "items": {"type": "object"}}},
          "required": ["sources"]}, _infer_data_flows),
    Tool("list_connectors", "List Tier-1 discovery connectors and the inputs each needs.",
         {"type": "object", "properties": {}}, _list_connectors),
    Tool("connector_policy", "Get the read-only least-privilege policy for a connector provider.",
         {"type": "object", "properties": {"provider": {"type": "string"}}, "required": ["provider"]},
         _connector_policy),
]

_BY_NAME: Dict[str, Tool] = {t.name: t for t in TOOLS}


def list_tools() -> List[Dict[str, Any]]:
    """Tool descriptors for the MCP list_tools response."""
    return [{"name": t.name, "description": t.description, "inputSchema": t.input_schema} for t in TOOLS]


def call_tool(name: str, arguments: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Dispatch a tool by name. Raises KeyError for unknown tool, ValueError for bad args."""
    tool = _BY_NAME.get(name)
    if tool is None:
        raise KeyError(f"Unknown tool '{name}'. Available: {list(_BY_NAME)}")
    return tool.handler(arguments or {})
