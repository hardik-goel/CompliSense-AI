"""Artefact provenance + staleness — does this document still reflect the current law?"""

from pathlib import Path

from agent.rules.loader import load_rulepack
from compliance.provenance import (
    assess_freshness,
    build_provenance,
    changed_fields,
    rule_fingerprint,
)

EXT = load_rulepack(Path("rulepacks/dpdp_india_extended_v2.yaml"), validate=False)

RULE = {
    "id": "DPDP-SEC5-NOTICE-001", "clause": "Section 5",
    "title": "Privacy notice covers processing essentials",
    "act_citation": "DPDP Act 2023, s.5 (Notice)",
    "rule_citation": "DPDP Rules 2025, Rule 3",
    "source_url": "https://dpdpa.com/x.pdf",
    "status": "phased_not_yet_in_force", "enforcement_date": "2027-05-13",
    "date_status": "phased_confirmed",
    "description": "Notice must itemise the personal data and the purpose.",
}


def _pack(*rules, version="2.1.0"):
    return {"pack_id": "dpdp_india_extended_v2", "pack_version": version, "rules": list(rules)}


# --- fingerprints ------------------------------------------------------------------------

def test_fingerprint_is_stable_across_identical_rules():
    assert rule_fingerprint(RULE) == rule_fingerprint(dict(RULE))


def test_fingerprint_changes_when_the_enforcement_date_moves():
    moved = {**RULE, "enforcement_date": "2028-01-01"}
    assert rule_fingerprint(moved) != rule_fingerprint(RULE)


def test_fingerprint_changes_when_the_citation_changes():
    assert rule_fingerprint({**RULE, "rule_citation": "Rule 4"}) != rule_fingerprint(RULE)


def test_fingerprint_ignores_cosmetic_fields_that_carry_no_legal_weight():
    # A reworded internal title is not a change in the law.
    assert rule_fingerprint({**RULE, "title": "Notice rule (reworded)"}) == rule_fingerprint(RULE)


def test_fingerprint_is_insensitive_to_key_order():
    reordered = {k: RULE[k] for k in reversed(list(RULE))}
    assert rule_fingerprint(reordered) == rule_fingerprint(RULE)


def test_changed_fields_names_exactly_what_moved():
    moved = {**RULE, "enforcement_date": "2028-01-01", "status": "in_force"}
    assert changed_fields(RULE, moved) == ["enforcement_date", "status"]


# --- stamping ------------------------------------------------------------------------------

def test_provenance_stamps_only_the_rules_the_artefact_depends_on():
    stamp = build_provenance(EXT, ["DPDP-SEC5-NOTICE-001", "DPDP-SEC16-TRANSFER-001"])
    assert set(stamp["rules"]) == {"DPDP-SEC5-NOTICE-001", "DPDP-SEC16-TRANSFER-001"}
    assert stamp["pack_id"] == "dpdp_india_extended_v2"
    assert stamp["pack_version"]


def test_provenance_records_a_dependency_the_pack_does_not_have():
    stamp = build_provenance(EXT, ["DPDP-SEC5-NOTICE-001", "DPDP-NOPE-001"])
    assert stamp["missing_rule_ids"] == ["DPDP-NOPE-001"]


def test_provenance_can_record_the_domains_the_artefact_covers():
    stamp = build_provenance(EXT, ["DPDP-SEC16-TRANSFER-001"], domains=[8])
    assert stamp["domains"] == [8]


# --- freshness -------------------------------------------------------------------------------

def test_unchanged_pack_is_fresh():
    pack = _pack(RULE)
    stamp = build_provenance(pack, ["DPDP-SEC5-NOTICE-001"])
    result = assess_freshness(stamp, pack)
    assert result["status"] == "fresh" and result["reasons"] == []


def test_a_changed_dependency_makes_the_artefact_stale_and_names_the_field():
    stamp = build_provenance(_pack(RULE), ["DPDP-SEC5-NOTICE-001"])
    moved = _pack({**RULE, "enforcement_date": "2028-01-01"}, version="2.2.0")
    result = assess_freshness(stamp, moved)
    assert result["status"] == "stale"
    reason = next(r for r in result["reasons"] if r["kind"] == "rule_changed")
    assert reason["rule_id"] == "DPDP-SEC5-NOTICE-001"
    assert reason["fields"] == ["enforcement_date"]


def test_a_removed_dependency_makes_the_artefact_stale():
    stamp = build_provenance(_pack(RULE), ["DPDP-SEC5-NOTICE-001"])
    result = assess_freshness(stamp, _pack(version="3.0.0"))
    assert result["status"] == "stale"
    assert any(r["kind"] == "rule_removed" for r in result["reasons"])


def test_a_pack_bump_that_leaves_your_rules_alone_is_review_not_stale():
    stamp = build_provenance(_pack(RULE), ["DPDP-SEC5-NOTICE-001"])
    other = {"id": "DPDP-SEC99-OTHER-001", "clause": "s.99"}
    result = assess_freshness(stamp, _pack(RULE, other, version="2.2.0"))
    assert result["status"] == "review"
    assert any(r["kind"] == "pack_version_changed" for r in result["reasons"])


def test_a_new_rule_inside_a_covered_domain_makes_the_artefact_stale():
    stamp = build_provenance(_pack(RULE), ["DPDP-SEC5-NOTICE-001"], domains=[8])
    transfer = {"id": "DPDP-SEC16-TRANSFER-001", "clause": "Section 16"}
    result = assess_freshness(stamp, _pack(RULE, transfer, version="2.2.0"))
    assert result["status"] == "stale"
    reason = next(r for r in result["reasons"] if r["kind"] == "new_rule_in_covered_domain")
    assert reason["rule_id"] == "DPDP-SEC16-TRANSFER-001" and reason["domain"] == 8


def test_a_new_rule_outside_the_covered_domains_does_not_make_it_stale():
    stamp = build_provenance(_pack(RULE), ["DPDP-SEC5-NOTICE-001"], domains=[2])
    transfer = {"id": "DPDP-SEC16-TRANSFER-001", "clause": "Section 16"}
    assert assess_freshness(stamp, _pack(RULE, transfer, version="2.2.0"))["status"] == "review"


def test_freshness_against_a_different_pack_is_reported_not_silently_compared():
    stamp = build_provenance(_pack(RULE), ["DPDP-SEC5-NOTICE-001"])
    other_pack = {"pack_id": "euai_core_v2", "pack_version": "1.0.0", "rules": [RULE]}
    result = assess_freshness(stamp, other_pack)
    assert any(r["kind"] == "pack_mismatch" for r in result["reasons"])


def test_every_reason_carries_human_guidance():
    stamp = build_provenance(_pack(RULE), ["DPDP-SEC5-NOTICE-001"])
    result = assess_freshness(stamp, _pack({**RULE, "status": "in_force"}, version="2.2.0"))
    assert all(r.get("action") for r in result["reasons"])


# --- closing the loop from a regwatch change to the artefacts it invalidates -------------

from compliance.provenance import impacted_artefacts  # noqa: E402


def _artefact(art_id, rule_ids, domains=None):
    return {"artefact_id": art_id,
            "provenance": build_provenance(EXT, rule_ids, domains=domains)}


def test_a_changed_rule_impacts_the_artefact_that_depends_on_it():
    arts = [_artefact("record_of_processing", ["DPDP-SEC16-TRANSFER-001"]),
            _artefact("privacy_notice", ["DPDP-SEC5-NOTICE-001"])]
    hits = impacted_artefacts(["DPDP-SEC16-TRANSFER-001"], arts)
    assert [h["artefact_id"] for h in hits] == ["record_of_processing"]
    assert hits[0]["via"] == "dependency"


def test_a_changed_rule_impacts_artefacts_covering_its_domain_even_without_a_direct_dependency():
    # The ROPA never cited SEC12, but it claims to cover domain 7 (data principal rights).
    arts = [_artefact("record_of_processing", ["DPDP-SEC16-TRANSFER-001"], domains=[7])]
    hits = impacted_artefacts(["DPDP-SEC12-CORRECTION-001"], arts)
    assert hits[0]["via"] == "domain"
    assert hits[0]["domains"] == [7]


def test_an_unrelated_rule_change_impacts_nothing():
    arts = [_artefact("record_of_processing", ["DPDP-SEC16-TRANSFER-001"], domains=[8])]
    assert impacted_artefacts(["DPDP-SEC9-CHILDREN-001"], arts) == []


def test_a_direct_dependency_wins_over_a_domain_match_for_the_same_artefact():
    arts = [_artefact("ropa", ["DPDP-SEC16-TRANSFER-001"], domains=[8])]
    hits = impacted_artefacts(["DPDP-SEC16-TRANSFER-001"], arts)
    assert len(hits) == 1 and hits[0]["via"] == "dependency"


def test_impact_lists_the_rules_that_caused_it_and_carries_guidance():
    arts = [_artefact("ropa", ["DPDP-SEC16-TRANSFER-001", "DPDP-SEC5-NOTICE-001"])]
    hits = impacted_artefacts(["DPDP-SEC16-TRANSFER-001", "DPDP-SEC5-NOTICE-001"], arts)
    # Sorted as strings, so SEC16 precedes SEC5.
    assert hits[0]["rule_ids"] == ["DPDP-SEC16-TRANSFER-001", "DPDP-SEC5-NOTICE-001"]
    assert hits[0]["action"]


def test_artefacts_without_a_provenance_stamp_are_reported_as_unverifiable():
    hits = impacted_artefacts(["DPDP-SEC5-NOTICE-001"], [{"artefact_id": "legacy_doc"}])
    assert hits[0]["via"] == "unstamped"


def test_a_stamp_taken_from_the_real_pack_is_immediately_fresh():
    # Regression: covered domains contain many rules the artefact never cited. Treating those
    # as "new" made every freshly generated artefact report stale on the same day.
    stamp = build_provenance(EXT, ["DPDP-SEC16-TRANSFER-001"], domains=[1, 2, 3, 4, 7, 8])
    assert assess_freshness(stamp, EXT)["status"] == "fresh"


def test_a_stamp_without_a_domain_baseline_stays_quiet_rather_than_crying_wolf():
    stamp = build_provenance(EXT, ["DPDP-SEC16-TRANSFER-001"], domains=[7])
    stamp.pop("domain_rules")
    assert assess_freshness(stamp, EXT)["status"] == "fresh"
