"""
DPDP Readiness scoring from a Tier-0 manifest (Phase 1.2).

Takes a manifest (questionnaire answers) and produces an honest readiness score + gap list,
reusing the Phase-0 rulepacks and applicability gating. Principles:

- **Applicability first.** Rules that don't apply to this entity (e.g. SDF-only duties for a
  non-SDF startup) are excluded from scoring — never counted as gaps.
- **Unknown is NOT ready.** If the manifest gives no evidence a control exists, the rule is a
  gap ("needs review"), never silently passed. We do not fabricate readiness.
- **Readiness language, not compliance.** Output frames items as ready / gap / prepare-by,
  with each rule's real citation + enforcement framing. Not a legal determination.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List

from compliance.manifest import Manifest, manifest_to_profile
from compliance.applicability import resolve_applicability
from agent.scoring.overall import readiness_framing

# rule_id -> predicate(manifest) -> True (ready) / False (gap) / None (unknown, needs review)
_PREDICATES: Dict[str, Callable[[Manifest], Any]] = {
    "DPDP-SEC5-NOTICE-001": lambda m: m.has_privacy_notice,
    "DPDP-SEC6-CONSENT-001": lambda m: m.consent_mechanism == "explicit_optin" and m.has_withdrawal_mechanism,
    "DPDP-SEC8-OBLIGATIONS-001": lambda m: m.has_security_safeguards,
    "DPDP-SEC8-OBLIGATIONS-002": lambda m: m.has_breach_process,
    "DPDP-SEC8-OBLIGATIONS-003": lambda m: m.retention_defined,
    "DPDP-SEC8-RETENTION-CLASS-001": lambda m: m.retention_defined,
    "DPDP-SEC13-GRIEVANCE-001": lambda m: m.has_grievance_contact,
    "DPDP-SEC8-PROCESSOR-001": lambda m: m.processors_listed,
    # EU AI Act posture predicates (manifest-declared; secondary-sourced, pending legal review).
    "EUAI-ART5-PROHIBITED-001": lambda m: m.avoids_prohibited_practices,
    "EUAI-ART4-LITERACY-001": lambda m: m.has_ai_literacy_program,
    "EUAI-ART50-TRANSPARENCY-001": lambda m: m.has_art50_transparency,
    "EUAI-ART9-RISK-MGMT-001": lambda m: m.has_risk_management_system,
    "EUAI-ART10-DATA-GOV-001": lambda m: m.has_data_governance,
    "EUAI-ART11-TECHDOC-001": lambda m: m.has_technical_documentation,
    "EUAI-ART11-TECHDOC-002": lambda m: m.has_technical_documentation,
    "EUAI-ART18-DATA-GOV-002": lambda m: m.has_recordkeeping_logs,
    "EUAI-ART20-RECORD-KEEPING-001": lambda m: m.has_recordkeeping_logs,
    # v2 citation-corrected IDs (Task 3): QMS->Art17, data-gov->Art10, logging->Art12/19.
    "EUAI-ART17-QUALITY-MGMT-001": lambda m: m.has_quality_management_system,
    "EUAI-ART10-DATA-GOV-002": lambda m: m.has_data_governance,
    "EUAI-ART12-RECORD-KEEPING-001": lambda m: m.has_recordkeeping_logs,
    "EUAI-ART13-TRANSPARENCY-001": lambda m: m.has_transparency_info,
    "EUAI-ART14-HUMAN-OVERSIGHT-001": lambda m: m.has_human_oversight,
    "EUAI-ART15-ACCURACY-001": lambda m: m.has_accuracy_robustness,
    "EUAI-ART16-QUALITY-MGMT-001": lambda m: m.has_quality_management_system,
    "EUAI-ART6-CLASSIFICATION-001": lambda m: m.has_risk_classification,
    "EUAI-ART43-CONFORMITY-001": lambda m: m.has_conformity_assessment,
    "EUAI-ART49-REGISTRATION-001": lambda m: m.registered_eu_database,
    "EUAI-ART72-POSTMARKET-001": lambda m: m.has_postmarket_monitoring,
    "EUAI-ART53-GPAI-001": lambda m: m.has_gpai_documentation,
    # Omnibus / deployer additions (v2 packs). Secondary-sourced, pending legal review.
    "EUAI-ART5-PROHIBITED-002": lambda m: m.avoids_prohibited_practices,
    "EUAI-ART50-LEGACY-MARKING-001": lambda m: m.has_art50_transparency,
    "EUAI-ART26-DEPLOYER-001": lambda m: m.has_deployer_obligations,
    "EUAI-ART27-FRIA-001": lambda m: m.has_fria,
    "EUAI-ART22-AUTHREP-001": lambda m: m.has_eu_authorised_rep,
    "EUAI-ART73-INCIDENT-001": lambda m: m.has_incident_reporting_procedure,
}

_SEVERITY_RANK = {"Critical": 0, "Major": 1, "Minor": 2, "unknown": 3}


def _evaluate_rule(rule: Dict[str, Any], manifest: Manifest) -> str:
    """Return 'ready' | 'gap' | 'unknown' for an applicable rule under the manifest."""
    pred = _PREDICATES.get(rule.get("id"))
    if pred is None:
        return "unknown"
    try:
        result = pred(manifest)
    except Exception:
        return "unknown"
    if result is None:
        return "unknown"
    return "ready" if result else "gap"


def score_manifest(manifest: Manifest, pack: Dict[str, Any]) -> Dict[str, Any]:
    """Score a manifest against a (loaded) rulepack. Returns a structured readiness report."""
    profile = manifest_to_profile(manifest)
    rules = pack.get("rules", [])

    ready: List[Dict[str, Any]] = []
    gaps: List[Dict[str, Any]] = []
    not_applicable: List[Dict[str, Any]] = []

    for rule in rules:
        applicable, reason = resolve_applicability(rule, profile)
        base = {
            "rule_id": rule.get("id"),
            "title": rule.get("title"),
            "clause": rule.get("clause"),
            "severity": rule.get("severity", "unknown"),
            "act_citation": rule.get("act_citation"),
            "rule_citation": rule.get("rule_citation"),
            "source_url": rule.get("source_url"),
            "enforcement_date": rule.get("enforcement_date"),
            "date_status": rule.get("date_status"),
            "verification": rule.get("verification"),
            "framing": readiness_framing(rule.get("enforcement_date"), rule.get("date_status")),
        }
        if not applicable:
            not_applicable.append({**base, "status": "NOT_APPLICABLE", "reason": reason})
            continue

        outcome = _evaluate_rule(rule, manifest)
        if outcome == "ready":
            ready.append({**base, "status": "READY"})
        else:
            gaps.append({
                **base,
                "status": "GAP" if outcome == "gap" else "NEEDS_REVIEW",
            })

    scored = len(ready) + len(gaps)
    jurisdiction = pack.get("jurisdiction", "DPDP_INDIA")

    # EU now has posture predicates, so the score is a real (manifest-declared) readiness
    # percentage — same "unknown = gap" honesty as DPDP. EU rules remain secondary-sourced and
    # PENDING legal review (flagged in the disclaimer), so the number is gated, not authoritative.
    scoring_available = True
    score = round(100 * len(ready) / scored) if scored else 0

    # Order gaps by severity so the teaser (top-3) shows the most important first.
    gaps.sort(key=lambda g: _SEVERITY_RANK.get(g["severity"], 9))
    if jurisdiction == "EU_AI_ACT":
        disclaimer = (
            "Readiness self-assessment, not legal advice and not a determination of "
            "compliance. EU AI Act prohibited-practices (Art. 5), literacy (Art. 4) and GPAI "
            "duties are in force; high-risk and Art. 50 transparency duties are deferred "
            "('prepare by' items, some PROVISIONAL pending the Digital Omnibus). EU rules here "
            "are secondary-sourced and PENDING professional legal review. Verify against "
            "primary sources and consult a qualified practitioner."
        )
    else:
        disclaimer = (
            "Readiness self-assessment, not legal advice and not a determination of "
            "compliance. DPDP operational obligations become enforceable ~13 May 2027; "
            "gaps are 'prepare by' items. Verify against primary sources and consult a "
            "qualified practitioner."
        )

    # Deliberate scope exclusions declared in the pack header — surfaced so an omission
    # reads as a decision ("Out of scope for your profile"), not a gap we missed.
    scope_exclusions = pack.get("scope_exclusions") or []

    return {
        "jurisdiction": jurisdiction,
        "pack_id": pack.get("pack_id"),
        "pack_version": pack.get("pack_version") or pack.get("version"),
        "rules_current_as_of": pack.get("rules_current_as_of") or pack.get("current_as_of"),
        "scope_exclusions": scope_exclusions,
        "readiness_score": score,
        "scoring_available": scoring_available,
        "obligations_identified": scored,
        "summary": {
            "ready": len(ready),
            "gaps": len(gaps),
            "applicable": scored,
            "not_applicable": len(not_applicable),
        },
        "ready": ready,
        "gaps": gaps,
        "not_applicable": not_applicable,
        "disclaimer": disclaimer,
    }


def top_gaps(report: Dict[str, Any], n: int = 3) -> List[Dict[str, Any]]:
    """Top-N gaps for the public teaser (already severity-ordered)."""
    return report.get("gaps", [])[:n]
