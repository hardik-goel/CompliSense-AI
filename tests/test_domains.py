"""The 8 DPDPA domains — the lens auditors and enterprise buyers already use."""

from pathlib import Path

import pytest

from agent.rules.loader import iter_rules, load_rulepack
from compliance.domains import (
    DOMAINS,
    applicable_domains,
    domain_by_number,
    domain_coverage,
    domains_for_node,
    domains_for_row,
)

CORE = load_rulepack(Path("rulepacks/dpdp_india_core_v1.yaml"), validate=False)
EXT = load_rulepack(Path("rulepacks/dpdp_india_extended_v2.yaml"), validate=False)


# --- the model ------------------------------------------------------------------------

def test_there_are_exactly_eight_domains_numbered_one_to_eight():
    assert len(DOMAINS) == 8
    assert [d["number"] for d in DOMAINS] == list(range(1, 9))


def test_every_domain_carries_an_act_citation():
    assert all(d["act_citation"] for d in DOMAINS)


def test_domains_cover_the_expected_dpdpa_subject_areas():
    ids = {d["domain_id"] for d in DOMAINS}
    assert ids == {"grounds_of_processing", "notice", "consent", "data_security",
                   "children_data", "sdf_obligations", "data_principal_rights",
                   "cross_border_transfer"}


def test_domain_lookup_by_number():
    assert domain_by_number(8)["domain_id"] == "cross_border_transfer"


def test_unknown_domain_number_raises():
    with pytest.raises(KeyError):
        domain_by_number(9)


# --- coverage is PROVEN against the rulepack, not asserted ------------------------------

def test_every_rule_in_the_extended_pack_belongs_to_a_domain():
    report = domain_coverage(EXT)
    assert report["uncovered_rule_ids"] == []


def test_every_rule_in_the_core_pack_belongs_to_a_domain():
    assert domain_coverage(CORE)["uncovered_rule_ids"] == []


def test_coverage_reports_which_rules_back_each_domain():
    by_domain = domain_coverage(EXT)["by_domain"]
    assert "DPDP-SEC16-TRANSFER-001" in by_domain["cross_border_transfer"]
    assert "DPDP-SEC5-NOTICE-001" in by_domain["notice"]


def test_a_domain_with_no_backing_rule_in_the_pack_is_reported_as_a_hole():
    thin = {"pack_id": "thin", "rules": [{"id": "DPDP-SEC5-NOTICE-001"}]}
    report = domain_coverage(thin)
    assert "cross_border_transfer" in report["domains_without_rules"]
    assert "notice" not in report["domains_without_rules"]


def test_coverage_flags_a_rule_the_domain_model_does_not_know():
    pack = {"pack_id": "x", "rules": [{"id": "DPDP-SEC99-BRAND-NEW-001"}]}
    assert domain_coverage(pack)["uncovered_rule_ids"] == ["DPDP-SEC99-BRAND-NEW-001"]


# --- applicability ----------------------------------------------------------------------

def test_children_and_sdf_domains_are_not_applicable_by_default():
    nums = applicable_domains({})
    assert 5 not in nums and 6 not in nums


def test_children_domain_becomes_applicable_when_children_data_is_processed():
    assert 5 in applicable_domains({"processes_children_data": True})


def test_sdf_domain_becomes_applicable_once_notified():
    assert 6 in applicable_domains({"notified_as_sdf": True})


def test_cross_border_domain_becomes_applicable_on_transfer():
    assert 8 in applicable_domains({"cross_border_transfer": True})


def test_core_domains_always_apply():
    assert {1, 2, 3, 4, 7} <= set(applicable_domains({}))


# --- per-stage overlay (this is what the deliverable pins to the diagram) -----------------

def test_a_store_row_carries_security_but_not_notice():
    row = {"store": "users_db", "categories": ["email"], "cross_border": False,
           "legal_basis": "consent"}
    nums = domains_for_row(row, {})
    assert 4 in nums and 2 not in nums


def test_a_cross_border_store_row_picks_up_domain_eight():
    row = {"store": "analytics", "categories": ["email"], "cross_border": True,
           "legal_basis": "consent"}
    assert 8 in domains_for_row(row, {})


def test_a_row_holding_childrens_data_picks_up_domain_five():
    row = {"store": "kids", "categories": ["children_data"], "cross_border": False,
           "legal_basis": "consent"}
    assert 5 in domains_for_row(row, {})


def test_collection_point_carries_notice_consent_and_grounds():
    nums = domains_for_node("principal", {}, {"consent_mechanism": "explicit_optin"})
    assert {1, 2, 3} <= set(nums)


def test_processing_activity_carries_grounds_and_data_principal_rights():
    nums = domains_for_node("activity", {}, {})
    assert 1 in nums and 7 in nums


def test_processor_node_carries_the_security_domain():
    assert 4 in domains_for_node("processor", {}, {})


def test_store_outside_india_gets_the_cross_border_badge():
    nums = domains_for_node("store", {"outside_india": True}, {})
    assert 4 in nums and 8 in nums


def test_store_inside_india_does_not_get_the_cross_border_badge():
    assert 8 not in domains_for_node("store", {"outside_india": False}, {})


def test_sdf_badge_appears_on_every_stage_once_notified():
    assert 6 in domains_for_node("store", {"outside_india": False}, {"notified_as_sdf": True})


def test_returned_domain_numbers_are_sorted_and_unique():
    nums = domains_for_node("store", {"outside_india": True},
                            {"notified_as_sdf": True, "processes_children_data": True})
    assert nums == sorted(set(nums))


# --- domain rollup over a readiness report ------------------------------------------------

from compliance.domains import domain_rollup  # noqa: E402
from compliance.manifest import build_manifest  # noqa: E402
from compliance.readiness import score_manifest  # noqa: E402

STARTUP = {"entity_type": "startup", "sector": "saas", "offers_in_india": True,
           "registered_users": 500, "consent_mechanism": "explicit_optin",
           "has_privacy_notice": True}


def _report(extra=None):
    return score_manifest(build_manifest({**STARTUP, **(extra or {})}), EXT)


def test_rollup_covers_all_eight_domains():
    assert [d["number"] for d in domain_rollup(_report())] == list(range(1, 9))


def test_a_declared_posture_shows_as_ready_in_its_domain():
    notice = next(d for d in domain_rollup(_report()) if d["number"] == 2)
    assert "DPDP-SEC5-NOTICE-001" in notice["ready"]
    assert notice["status"] == "ready"


def test_an_undeclared_posture_shows_as_a_gap_in_its_domain():
    notice = next(d for d in domain_rollup(_report({"has_privacy_notice": False}))
                  if d["number"] == 2)
    assert "DPDP-SEC5-NOTICE-001" in notice["gaps"]
    assert notice["status"] == "gap"


def test_a_domain_gated_off_by_the_profile_is_reported_not_applicable():
    sdf = next(d for d in domain_rollup(_report()) if d["number"] == 6)
    assert sdf["applicable"] is False and sdf["status"] == "not_applicable"


def test_a_domain_becomes_applicable_once_the_profile_triggers_it():
    sdf = next(d for d in domain_rollup(_report({"notified_as_sdf": True}))
               if d["number"] == 6)
    assert sdf["applicable"] is True and sdf["status"] != "not_applicable"


def test_a_partly_ready_domain_reports_partial_with_a_percentage():
    rollup = domain_rollup(_report({"has_security_safeguards": True}))
    security = next(d for d in rollup if d["number"] == 4)
    assert security["status"] == "partial"
    assert 0 < security["percent"] < 100


def test_each_domain_carries_its_citation_so_the_rollup_is_defensible():
    assert all(d["act_citation"] for d in domain_rollup(_report()))


def test_rollup_counts_reconcile_with_the_rules_it_lists():
    for d in domain_rollup(_report()):
        assert d["assessed"] == len(d["ready"]) + len(d["gaps"])


def test_the_lens_is_dpdp_only_and_says_so_rather_than_guessing_for_the_eu():
    eu = score_manifest(build_manifest({"has_ai_system": True, "eu_role": "provider",
                                        "provides_to_eu": True}), EU_PACK)
    assert domain_rollup(eu) == []


EU_PACK = load_rulepack(Path("rulepacks/euai_extended_v2.yaml"), validate=False)
