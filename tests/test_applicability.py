"""Tests for applicability gating (compliance/applicability.py) and scanner integration."""

from pathlib import Path

from compliance.applicability import resolve_applicability, default_profile
from agent.scanner import run_scan


def _rule(rule_id, scope):
    return {
        "id": rule_id,
        "clause": "Section X",
        "title": rule_id,
        "evaluator": "file_presence",
        "applicability": {"scope": scope, "threshold": None, "exemption_ref": None},
        "inputs": {"file": "compliance/does_not_exist.json", "required_json_fields": ["a"]},
        "expression": "exists and missing_fields <= 1",
        "thresholds": {"pass": 0.0, "partial": 2.0},
        "severity": "Major",
    }


def test_no_profile_means_everything_applies():
    ok, reason = resolve_applicability(_rule("R", "significant_data_fiduciary_only"), None)
    assert ok is True
    assert "inactive" in reason


def test_universal_scope_always_applies():
    ok, _ = resolve_applicability(_rule("R", "all_data_fiduciaries"), default_profile())
    assert ok is True


def test_sdf_rule_not_applicable_for_non_sdf():
    ok, reason = resolve_applicability(
        _rule("R", "significant_data_fiduciary_only"), default_profile()
    )
    assert ok is False
    assert "is_significant_data_fiduciary" in reason


def test_sdf_rule_applies_when_flagged():
    profile = default_profile()
    profile["is_significant_data_fiduciary"] = True
    ok, _ = resolve_applicability(_rule("R", "significant_data_fiduciary_only"), profile)
    assert ok is True


def test_eu_provider_rule_not_applicable_for_deployer_only():
    ok, reason = resolve_applicability(_rule("R", "eu_provider"), default_profile())
    assert ok is False
    assert "eu_provider" in reason


def test_eu_provider_rule_applies_when_role_declared():
    profile = default_profile()
    profile["eu_roles"] = ["eu_provider"]
    ok, _ = resolve_applicability(_rule("R", "eu_provider"), profile)
    assert ok is True


def test_legacy_rule_without_scope_applies():
    ok, _ = resolve_applicability({"id": "R"}, default_profile())
    assert ok is True


def test_run_scan_marks_non_applicable(tmp_path: Path):
    rules = [
        _rule("UNIVERSAL", "all_data_fiduciaries"),
        _rule("SDF-ONLY", "significant_data_fiduciary_only"),
        _rule("EU-PROVIDER", "eu_provider"),
    ]
    out = run_scan(tmp_path, rules, entity_profile=default_profile())
    statuses = {r["rule_id"]: r["status"] for r in out["results"]}

    # SDF-only and EU-provider don't apply to a default startup → NOT_APPLICABLE, not a gap.
    assert statuses["SDF-ONLY"] == "NOT_APPLICABLE"
    assert statuses["EU-PROVIDER"] == "NOT_APPLICABLE"
    # Universal rule is evaluated (file missing → MISSING, i.e. a real gap surfaced).
    assert statuses["UNIVERSAL"] in ("MISSING", "FAIL")
    assert out["summary"]["not_applicable"] == 2


def test_run_scan_without_profile_evaluates_all(tmp_path: Path):
    rules = [_rule("SDF-ONLY", "significant_data_fiduciary_only")]
    out = run_scan(tmp_path, rules)  # no profile → gating inactive
    assert out["results"][0]["status"] != "NOT_APPLICABLE"
    assert out["summary"]["not_applicable"] == 0
