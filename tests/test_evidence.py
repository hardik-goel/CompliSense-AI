"""Evidence pack assembler (Phase 8) — pure."""

from compliance.evidence import DISCLAIMER, build_evidence_pack

PROJECT = {"id": "p1", "name": "Acme", "compliance_standard": "DPDP_INDIA", "team_id": "team_1",
           "discovered_manifest": {"has_security_safeguards": True, "storage_locations": ["aws"]}}

READINESS = {
    "readiness_score": 60,
    "summary": {"ready": 3, "gaps": 2, "applicable": 5, "not_applicable": 1},
    "ready": [{"rule_id": "R1", "title": "Notice", "act_citation": "s.5", "rule_citation": "Rule 3",
               "source_url": "http://law/a", "verification": "primary"}],
    "gaps": [{"rule_id": "R2", "title": "Breach process", "act_citation": "s.8", "rule_citation": "Rule 7",
              "status": "GAP", "framing": "Prepare by 2027-05-13.", "source_url": "http://law/b"}],
    "not_applicable": [],
}
RUNS = [{"created_at": "2026-06-02", "score": 60, "scan_id": "s2"},
        {"created_at": "2026-06-01", "score": 50, "scan_id": "s1"}]
ALERTS = [{"status": "open", "message": "2 rules regressed"}, {"status": "acknowledged", "message": "old"}]
DISCOVERIES = [{"provider": "aws", "created_at": "2026-06-01", "signals": [1, 2], "suggestions": [1],
                "applied_fields": ["has_security_safeguards"]}]
PII = [{"report": {"category_to_sources": {"email": ["db"], "government_id": ["kyc"]}, "has_cross_border": True}}]


def test_pack_structure_and_provenance():
    pack = build_evidence_pack(PROJECT, READINESS, RUNS, ALERTS, DISCOVERIES, PII,
                               generated_at="2026-06-27T00:00:00", prepared_by="owner@x.com")
    assert pack["meta"]["project_name"] == "Acme"
    assert pack["meta"]["generated_at"] == "2026-06-27T00:00:00"
    assert pack["meta"]["prepared_by"] == "owner@x.com"
    assert pack["disclaimer"] == DISCLAIMER
    assert pack["readiness"]["score"] == 60


def test_citations_collected_and_deduped():
    pack = build_evidence_pack(PROJECT, READINESS, RUNS, ALERTS, DISCOVERIES, PII, generated_at="t")
    rule_ids = {c["rule_id"] for c in pack["citations"]}
    assert rule_ids == {"R1", "R2"}
    r2 = next(c for c in pack["citations"] if c["rule_id"] == "R2")
    assert r2["source_url"] == "http://law/b" and r2["rule_citation"] == "Rule 7"


def test_posture_history_and_monitoring():
    pack = build_evidence_pack(PROJECT, READINESS, RUNS, ALERTS, DISCOVERIES, PII, generated_at="t")
    assert [h["score"] for h in pack["posture_history"]] == [60, 50]
    assert pack["monitoring"]["open_alerts"] == 1
    assert pack["monitoring"]["scans_recorded"] == 2


def test_pii_and_discovery_summary():
    pack = build_evidence_pack(PROJECT, READINESS, RUNS, ALERTS, DISCOVERIES, PII, generated_at="t")
    assert set(pack["pii_data_flow"]["categories"]) == {"email", "government_id"}
    assert pack["pii_data_flow"]["cross_border_flagged"] is True
    assert pack["connector_discovery"][0]["provider"] == "aws"
    assert pack["confirmed_manifest"]["has_security_safeguards"] is True


def test_rulepack_and_governance_in_pack():
    gap_states = [{"rule_id": "R2", "status": "signed_off", "assignee_user_id": "u2",
                   "signed_off_by_email": "admin@x.com", "signed_off_at": "2026-06-28"}]
    pack = build_evidence_pack(PROJECT, READINESS, RUNS, ALERTS, DISCOVERIES, PII, generated_at="t",
                               rulepack_id="dpdp_india_core_v1", gap_states=gap_states)
    assert pack["meta"]["rulepack_applied"] == "dpdp_india_core_v1"
    assert pack["governance"]["signed_off_count"] == 1
    assert pack["governance"]["assignments"][0]["signed_off_by_email"] == "admin@x.com"


def test_no_credentials_or_raw_values_leak():
    # Discovery summary carries counts + applied field names, never signal/credential payloads.
    pack = build_evidence_pack(PROJECT, READINESS, RUNS, ALERTS, DISCOVERIES, PII, generated_at="t")
    d = pack["connector_discovery"][0]
    assert d["signals"] == 2 and "signal_values" not in d and "credentials" not in d


# --- the eight-domain lens travels into the evidence pack ---------------------------------

def test_evidence_pack_carries_the_domain_rollup_for_a_dpdp_assessment():
    from pathlib import Path
    from agent.rules.loader import load_rulepack
    from compliance.evidence import build_evidence_pack
    from compliance.manifest import build_manifest
    from compliance.readiness import score_manifest

    pack = load_rulepack(Path("rulepacks/dpdp_india_extended_v2.yaml"), validate=False)
    report = score_manifest(build_manifest(
        {"entity_type": "startup", "sector": "saas", "offers_in_india": True,
         "has_privacy_notice": True}), pack)
    out = build_evidence_pack({"id": "p1"}, report, [], [], [], [],
                              generated_at="2026-08-11T00:00:00Z")
    domains = out["readiness"]["domains"]
    assert [d["number"] for d in domains] == list(range(1, 9))
    assert next(d for d in domains if d["number"] == 2)["status"] == "ready"


def test_evidence_pack_omits_the_lens_for_a_non_dpdp_assessment():
    from pathlib import Path
    from agent.rules.loader import load_rulepack
    from compliance.evidence import build_evidence_pack
    from compliance.manifest import build_manifest
    from compliance.readiness import score_manifest

    pack = load_rulepack(Path("rulepacks/euai_extended_v2.yaml"), validate=False)
    report = score_manifest(build_manifest(
        {"has_ai_system": True, "eu_role": "provider", "provides_to_eu": True}), pack)
    out = build_evidence_pack({"id": "p1"}, report, [], [], [], [],
                              generated_at="2026-08-11T00:00:00Z")
    assert out["readiness"]["domains"] == []
