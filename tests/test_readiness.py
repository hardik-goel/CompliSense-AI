"""DPDP readiness scoring from a manifest (Phase 1.2)."""

from pathlib import Path

from compliance.manifest import build_manifest
from compliance.readiness import score_manifest, top_gaps
from agent.rules.loader import load_rulepack

PACK = load_rulepack(Path("rulepacks/dpdp_india_core_v1.yaml"), validate=False)
EXT_PACK = load_rulepack(Path("rulepacks/dpdp_india_extended_v1.yaml"), validate=False)
EU_PACK = load_rulepack(Path("rulepacks/euai_extended_v1.yaml"), validate=False)


def _ids(report, bucket):
    return {r["rule_id"] for r in report[bucket]}


def test_eu_posture_predicates_score():
    base = {"has_ai_system": True, "eu_role": "provider", "provides_to_eu": True}
    empty = score_manifest(build_manifest(base), EU_PACK)
    assert empty["jurisdiction"] == "EU_AI_ACT" and empty["scoring_available"] is True
    # No posture declared -> applicable EU rules are gaps (ready 0).
    assert empty["summary"]["applicable"] > 0 and empty["summary"]["ready"] == 0
    # Declare provider posture -> those rules become ready.
    strong = score_manifest(build_manifest({
        **base, "has_risk_management_system": True, "has_human_oversight": True,
        "has_technical_documentation": True, "has_accuracy_robustness": True,
        "avoids_prohibited_practices": True, "has_ai_literacy_program": True,
    }), EU_PACK)
    assert strong["readiness_score"] > empty["readiness_score"]
    ready_ids = {r["rule_id"] for r in strong["ready"]}
    assert "EUAI-ART9-RISK-MGMT-001" in ready_ids and "EUAI-ART5-PROHIBITED-001" in ready_ids


def test_class_retention_rule_gated_to_third_schedule_class():
    # Non-class startup: the 3-yr class erasure rule is NOT_APPLICABLE.
    startup = build_manifest({"entity_type": "startup", "sector": "saas", "registered_users": 100})
    r1 = score_manifest(startup, EXT_PACK)
    assert "DPDP-SEC8-RETENTION-CLASS-001" in _ids(r1, "not_applicable")

    # E-commerce with >=2cr users IS a Third-Schedule class -> rule applies and is a gap.
    klass = build_manifest({"entity_type": "enterprise", "sector": "ecommerce",
                            "registered_users": 25_000_000, "retention_defined": False})
    r2 = score_manifest(klass, EXT_PACK)
    assert "DPDP-SEC8-RETENTION-CLASS-001" in (_ids(r2, "gaps") | _ids(r2, "ready"))
    assert "DPDP-SEC8-RETENTION-CLASS-001" not in _ids(r2, "not_applicable")


def test_empty_startup_scores_low_with_gaps():
    m = build_manifest({"entity_type": "startup", "notified_as_sdf": False,
                        "processes_children_data": False})
    report = score_manifest(m, PACK)
    assert report["readiness_score"] == 0
    # SDF + children rules excluded for a typical startup → not counted as gaps
    na_ids = {r["rule_id"] for r in report["not_applicable"]}
    assert "DPDP-SEC10-SDF-001" in na_ids
    assert "DPDP-SEC9-CHILDREN-001" in na_ids
    # core scored rules (notice, consent, security, breach, grievance) are all gaps
    assert report["summary"]["gaps"] == report["summary"]["applicable"]


def test_well_prepared_startup_scores_high():
    m = build_manifest({
        "entity_type": "startup",
        "has_privacy_notice": True,
        "consent_mechanism": "explicit_optin",
        "has_withdrawal_mechanism": True,
        "has_security_safeguards": True,
        "has_breach_process": True,
        "has_grievance_contact": True,
    })
    report = score_manifest(m, PACK)
    assert report["readiness_score"] == 100
    assert report["summary"]["gaps"] == 0


def test_unknown_is_not_counted_ready():
    # No posture answers at all → everything applicable is a gap, score 0 (never silently ready).
    m = build_manifest({"entity_type": "startup"})
    report = score_manifest(m, PACK)
    assert report["readiness_score"] == 0
    assert all(g["status"] in ("GAP", "NEEDS_REVIEW") for g in report["gaps"])


def test_gaps_severity_ordered_and_teaser():
    m = build_manifest({"entity_type": "startup", "has_privacy_notice": False})
    report = score_manifest(m, PACK)
    teaser = top_gaps(report, 3)
    assert len(teaser) == 3
    # Critical gaps come before Major
    sev = [g["severity"] for g in report["gaps"]]
    assert sev == sorted(sev, key=lambda s: {"Critical": 0, "Major": 1}.get(s, 9))


def test_each_gap_carries_citation_and_framing():
    m = build_manifest({"entity_type": "startup"})
    report = score_manifest(m, PACK)
    for g in report["gaps"]:
        assert g["act_citation"] or g["rule_citation"]
        assert "prepare by" in g["framing"].lower() or "enforceable" in g["framing"].lower()


def test_sdf_startup_includes_sdf_rule():
    m = build_manifest({"entity_type": "enterprise", "notified_as_sdf": True})
    report = score_manifest(m, PACK)
    scored_ids = {r["rule_id"] for r in report["ready"] + report["gaps"]}
    assert "DPDP-SEC10-SDF-001" in scored_ids
