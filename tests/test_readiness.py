"""DPDP readiness scoring from a manifest (Phase 1.2)."""

from pathlib import Path

from compliance.manifest import build_manifest
from compliance.readiness import score_manifest, top_gaps
from agent.rules.loader import load_rulepack

PACK = load_rulepack(Path("rulepacks/dpdp_india_core_v1.yaml"), validate=False)


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
