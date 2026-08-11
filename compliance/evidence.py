"""Regulator-ready evidence pack assembler (Phase 8) — pure, no I/O.

Assembles a single, grounded, timestamped snapshot of a project's readiness posture from
data the API layer has already fetched: the readiness report (with citations), posture
history, monitoring alerts, connector-discovery summaries, PII inferences, and the confirmed
manifest. Output is structured for a regulator/auditor — every claim carries its citation and
enforcement framing, and the whole pack is wrapped in the standard readiness disclaimer.

Privacy: summaries only — no credentials, no raw artefacts, no personal-data values (the
inputs are already non-PII by construction).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

DISCLAIMER = (
    "This is a readiness self-assessment evidence pack, not legal advice and not a "
    "determination of compliance. Findings are 'prepare-by' readiness items framed against "
    "each rule's enforcement date. Verify against primary sources and have counsel review."
)


from compliance.domains import domain_rollup


def _citations_from_readiness(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    for bucket in ("ready", "gaps", "not_applicable"):
        for item in report.get(bucket, []) or []:
            rid = item.get("rule_id")
            if rid and rid not in seen:
                seen[rid] = {
                    "rule_id": rid,
                    "title": item.get("title"),
                    "act_citation": item.get("act_citation"),
                    "rule_citation": item.get("rule_citation"),
                    "source_url": item.get("source_url"),
                    "verification": item.get("verification"),
                    "enforcement_date": item.get("enforcement_date"),
                    "framing": item.get("framing"),
                }
    return list(seen.values())


def build_evidence_pack(
    project: Dict[str, Any],
    readiness_report: Dict[str, Any],
    runs: List[Dict[str, Any]],
    alerts: List[Dict[str, Any]],
    discoveries: List[Dict[str, Any]],
    pii_inferences: List[Dict[str, Any]],
    generated_at: str,
    prepared_by: Optional[str] = None,
    rulepack_id: Optional[str] = None,
    gap_states: Optional[List[Dict[str, Any]]] = None,
    pack_version: Optional[str] = None,
    rules_current_as_of: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the structured evidence pack. ``generated_at`` is an ISO string (injected).

    ``pack_version`` + ``rules_current_as_of`` carry the rulepack freshness stamp so the pack
    states which pack version it was assessed against and how current the legal content is.
    """
    discovered = project.get("discovered_manifest") or {}
    _pack_version = pack_version or "unknown"
    _rules_current = rules_current_as_of or "unknown"
    freshness_footer = (
        f"Readiness assessment against {rulepack_id or 'unknown'} {_pack_version}, "
        f"rules current as of {_rules_current}. Not legal advice; no compliance determination."
    )

    posture_history = [
        {"at": r.get("created_at"), "score": r.get("score"), "scan_id": r.get("scan_id")}
        for r in runs if r.get("score") is not None
    ]

    discovery_summary = [
        {"provider": d.get("provider"), "at": d.get("created_at"),
         "signals": len(d.get("signals", [])), "suggestions": len(d.get("suggestions", [])),
         "applied_fields": d.get("applied_fields", [])}
        for d in discoveries
    ]

    pii_categories = sorted({c for d in pii_inferences for c in
                             (d.get("report", {}).get("category_to_sources", {}) or {}).keys()})
    cross_border = any(d.get("report", {}).get("has_cross_border") for d in pii_inferences)

    open_alerts = [a for a in alerts if a.get("status") == "open"]

    gap_states = gap_states or []
    governance = {
        "assignments": [
            {"rule_id": g.get("rule_id"), "status": g.get("status"),
             "assignee_user_id": g.get("assignee_user_id"), "assigned_by": g.get("assigned_by"),
             "signed_off_by": g.get("signed_off_by"), "signed_off_by_email": g.get("signed_off_by_email"),
             "signed_off_at": g.get("signed_off_at"), "signoff_note": g.get("signoff_note")}
            for g in gap_states
        ],
        "signed_off_count": sum(1 for g in gap_states if g.get("status") == "signed_off"),
    }

    return {
        "meta": {
            "title": "CompliSense-AI Regulator-Ready Evidence Pack",
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "compliance_standard": project.get("compliance_standard"),
            "rulepack_applied": rulepack_id,
            "pack_version": _pack_version,
            "rules_current_as_of": _rules_current,
            "freshness_footer": freshness_footer,
            "generated_at": generated_at,
            "prepared_by": prepared_by,
            "team_id": project.get("team_id"),
        },
        "governance": governance,
        "readiness": {
            "score": readiness_report.get("readiness_score"),
            "summary": readiness_report.get("summary"),
            "gaps": readiness_report.get("gaps", []),
            "ready": readiness_report.get("ready", []),
            "not_applicable": readiness_report.get("not_applicable", []),
            # "Out of scope for your profile" — deliberate exclusions, not misses.
            "scope_exclusions": readiness_report.get("scope_exclusions", []),
            # The same findings re-cut by the eight DPDPA domains an auditor reads by.
            # Empty for a non-DPDP assessment rather than guessed.
            "domains": domain_rollup(readiness_report),
        },
        "confirmed_manifest": discovered,
        "posture_history": posture_history,
        "monitoring": {
            "scans_recorded": len(runs),
            "latest_score": runs[0].get("score") if runs else None,
            "open_alerts": len(open_alerts),
            "open_alert_titles": [a.get("message") for a in open_alerts[:10]],
        },
        "connector_discovery": discovery_summary,
        "pii_data_flow": {"categories": pii_categories, "cross_border_flagged": cross_border},
        "citations": _citations_from_readiness(readiness_report),
        "disclaimer": DISCLAIMER,
    }
