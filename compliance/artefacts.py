"""Artefact generator catalog (Tier-1.5) — pure.

For a client who has no compliance artefacts (a small team that doesn't know how to write a
privacy notice, retention schedule, etc.), this maps each readiness GAP to the artefact that
would close it, and declares **where each artefact can be sourced from**. The product can only
auto-fetch facts from a few places — everything else is the client's questionnaire answers, an
AI draft they must review, or something only the client can provide. This module makes that
explicit so the client is never misled about what we can/can't connect to.

It is a catalog + resolver only — the actual drafting is done by the copilot (LLM), and every
generated artefact is a DRAFT that the client must explicitly approve before use.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Where an artefact's content can come from. We can ONLY auto-connect to the Tier-1 connectors;
# be honest about the rest.
SOURCE_LABELS: Dict[str, str] = {
    "connector_discovery": "Auto-filled from your connected cloud (AWS / GCP / Azure / GitHub, read-only)",
    "manifest": "From your questionnaire answers (the Tier-0 manifest)",
    "ai_draft": "AI-drafted from your confirmed facts — you review & approve before use",
    "manual": "Manual — only you can provide this; we cannot fetch it",
}

# The places we CAN connect to (everything else is manifest answers or manual upload).
CONNECTABLE_SOURCES = ["AWS", "GCP", "Azure", "GitHub"]

# rule_id -> artefact spec. `filename` is what to drop into the scan input folder; `sources`
# lists where it can come from (in priority order); `manual_note` flags what only the client has.
ARTEFACT_CATALOG: Dict[str, Dict[str, Any]] = {
    "DPDP-SEC5-NOTICE-001": {
        "artefact_id": "privacy_notice", "title": "Privacy notice (DPDP)",
        "filename": "privacy_notice.md", "sources": ["manifest", "ai_draft"]},
    "DPDP-SEC6-CONSENT-001": {
        "artefact_id": "consent_policy", "title": "Consent & withdrawal policy",
        "filename": "consent_policy.md", "sources": ["manifest", "ai_draft"]},
    "DPDP-SEC8-OBLIGATIONS-001": {
        "artefact_id": "security_safeguards", "title": "Security safeguards document",
        "filename": "security_safeguards.md", "sources": ["connector_discovery", "manifest", "ai_draft"]},
    "DPDP-SEC8-OBLIGATIONS-002": {
        "artefact_id": "breach_process", "title": "Personal-data-breach response process",
        "filename": "breach_response_process.md", "sources": ["ai_draft"],
        "manual_note": "The actual breach register / incident log is manual — only you have it."},
    "DPDP-SEC8-OBLIGATIONS-003": {
        "artefact_id": "retention_schedule", "title": "Retention & erasure schedule",
        "filename": "retention_schedule.md", "sources": ["manifest", "ai_draft"]},
    "DPDP-SEC13-GRIEVANCE-001": {
        "artefact_id": "grievance_redressal", "title": "Grievance redressal note",
        "filename": "grievance_redressal.md", "sources": ["manifest", "ai_draft"]},
    "DPDP-SEC8-PROCESSOR-001": {
        "artefact_id": "processor_inventory", "title": "Processor / vendor inventory",
        "filename": "processor_inventory.md", "sources": ["ai_draft", "manual"],
        "manual_note": "Your vendor list + signed data-processing agreements are manual."},
    # EU AI Act (provider documentation)
    "EUAI-ART11-TECHDOC-001": {
        "artefact_id": "technical_documentation", "title": "AI technical documentation (Art. 11)",
        "filename": "technical_documentation.md", "sources": ["ai_draft", "manual"]},
    "EUAI-ART9-RISK-MGMT-001": {
        "artefact_id": "risk_management", "title": "AI risk-management system (Art. 9)",
        "filename": "risk_management_system.md", "sources": ["ai_draft"]},
    "EUAI-ART14-HUMAN-OVERSIGHT-001": {
        "artefact_id": "human_oversight", "title": "Human-oversight measures (Art. 14)",
        "filename": "human_oversight.md", "sources": ["ai_draft"]},
}


def _connector_source_available(project: Dict[str, Any]) -> bool:
    """True if the project has any confirmed discovery facts to pre-fill from."""
    return bool(project.get("discovered_manifest"))


def needed_artefacts(gap_rule_ids: List[str], project: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Map a project's gap rule_ids to the artefacts that would close them, with sources.

    Each entry lists the sources it can come from (with human labels), flags whether the
    connector source is actually available for THIS project, and carries any manual note.
    """
    have_connector = _connector_source_available(project)
    out: List[Dict[str, Any]] = []
    seen: set = set()
    for rule_id in gap_rule_ids:
        spec = ARTEFACT_CATALOG.get(rule_id)
        if not spec or spec["artefact_id"] in seen:
            continue
        seen.add(spec["artefact_id"])
        sources = [
            {"source": s, "label": SOURCE_LABELS[s],
             "available": (s != "connector_discovery") or have_connector}
            for s in spec["sources"]
        ]
        out.append({
            "artefact_id": spec["artefact_id"],
            "rule_id": rule_id,
            "title": spec["title"],
            "filename": spec["filename"],
            "draftable": "ai_draft" in spec["sources"],
            "sources": sources,
            "manual_note": spec.get("manual_note"),
        })
    return out


def spec_for(artefact_id: str) -> Dict[str, Any] | None:
    """Look up the catalog spec (with its rule_id) by artefact_id."""
    for rule_id, spec in ARTEFACT_CATALOG.items():
        if spec["artefact_id"] == artefact_id:
            return {**spec, "rule_id": rule_id}
    return None
