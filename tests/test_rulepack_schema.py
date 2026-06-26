"""Tests for the rulepack schema-v2 validator (compliance/rulepack_schema.py)."""

from pathlib import Path

import pytest

from compliance.rulepack_schema import (
    assert_valid,
    validate_pack,
    validate_rule,
    RulepackValidationError,
)
from agent.rules.loader import load_rulepack

REPO_ROOT = Path(__file__).resolve().parents[1]
RULEPACKS = REPO_ROOT / "rulepacks"
ALL_PACKS = sorted(RULEPACKS.glob("*.yaml"))


def _valid_rule(**overrides):
    rule = {
        "id": "DPDP-TEST-001",
        "evaluator": "file_presence",
        "act_citation": "DPDP Act 2023, s.5",
        "rule_citation": "DPDP Rules 2025, Rule 3",
        "source_url": "https://dpdpa.com/DPDP_Rules_2025_English_only.pdf",
        "applicability": {"scope": "all_data_fiduciaries", "threshold": None, "exemption_ref": None},
        "status": "phased_not_yet_in_force",
        "enforcement_date": "2027-05-13",
        "date_status": "phased_confirmed",
        "verification": "primary_source_verified",
    }
    rule.update(overrides)
    return rule


def _valid_pack(rules):
    return {
        "pack_id": "test_pack",
        "schema_version": 2,
        "current_as_of": "2026-06-26",
        "legal_review_status": "pending",
        "legal_review_note": "pending legal review; not legal advice",
        "rules": rules,
    }


def test_valid_rule_has_no_issues():
    assert validate_rule(_valid_rule()) == []


def test_missing_applicability_flagged():
    rule = _valid_rule()
    del rule["applicability"]
    issues = validate_rule(rule)
    assert any("applicability" in i for i in issues)


def test_bad_applicability_scope_flagged():
    rule = _valid_rule(applicability={"scope": "everyone"})
    issues = validate_rule(rule)
    assert any("scope" in i for i in issues)


def test_requires_at_least_one_citation():
    rule = _valid_rule(act_citation=None, rule_citation=None)
    issues = validate_rule(rule)
    assert any("citation" in i for i in issues)


def test_only_rule_citation_is_allowed():
    # Dual-layer is ideal, but at least one is the hard requirement.
    rule = _valid_rule(act_citation=None)
    assert validate_rule(rule) == []


def test_bad_source_url_flagged():
    rule = _valid_rule(source_url="dpdpa.com")
    assert any("source_url" in i for i in validate_rule(rule))


def test_null_enforcement_date_requires_in_force_status():
    bad = _valid_rule(enforcement_date=None, status="phased_not_yet_in_force")
    assert any("enforcement_date" in i for i in validate_rule(bad))
    good = _valid_rule(enforcement_date=None, status="in_force", date_status="in_force")
    assert validate_rule(good) == []


def test_bad_enum_values_flagged():
    rule = _valid_rule(status="live", date_status="soon", verification="trust_me")
    issues = validate_rule(rule)
    assert any("status" in i for i in issues)
    assert any("date_status" in i for i in issues)
    assert any("verification" in i for i in issues)


def test_pack_missing_fields_flagged():
    pack = _valid_pack([_valid_rule()])
    del pack["legal_review_note"]
    result = validate_pack(pack)
    assert not result.ok
    assert any("legal_review_note" in e for e in result.pack_errors)


def test_assert_valid_raises_on_bad_pack():
    pack = _valid_pack([_valid_rule(applicability={"scope": "nope"})])
    with pytest.raises(RulepackValidationError):
        assert_valid(pack)


@pytest.mark.parametrize("pack_path", ALL_PACKS, ids=lambda p: p.name)
def test_shipped_rulepacks_are_v2_valid(pack_path):
    pack = load_rulepack(pack_path, validate=False)
    result = validate_pack(pack)
    assert result.ok, result.summary()
