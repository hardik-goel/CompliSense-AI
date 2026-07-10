"""Tier-0 manifest model + questionnaire (Phase 1.1)."""

from compliance.manifest import (
    build_manifest,
    manifest_to_profile,
    is_third_schedule_class,
    validate_answers,
    get_questionnaire,
    QUESTION_IDS,
)
from compliance.applicability import resolve_applicability


def test_build_manifest_coerces_types():
    m = build_manifest({
        "entity_type": "startup",
        "offers_in_india": "yes",
        "registered_users": "1500",
        "notified_as_sdf": "false",
        "pii_categories": ["email", "phone"],
        "processes_children_data": True,
    })
    assert m.offers_in_india is True
    assert m.registered_users == 1500
    assert m.notified_as_sdf is False
    assert m.pii_categories == ["email", "phone"]
    assert m.processes_children_data is True


def test_build_manifest_ignores_unknown_keys():
    m = build_manifest({"bogus_key": "x", "entity_type": "enterprise"})
    assert m.entity_type == "enterprise"
    assert not hasattr(m, "bogus_key")


def test_third_schedule_trigger():
    assert is_third_schedule_class(build_manifest({"sector": "ecommerce", "registered_users": 25_000_000}))
    assert not is_third_schedule_class(build_manifest({"sector": "ecommerce", "registered_users": 5_000}))
    # gaming has a lower (50 lakh) trigger
    assert is_third_schedule_class(build_manifest({"sector": "online_gaming", "registered_users": 6_000_000}))
    # a normal saas startup is never a third-schedule class
    assert not is_third_schedule_class(build_manifest({"sector": "saas", "registered_users": 99_000_000}))


def test_manifest_to_profile_for_typical_startup():
    profile = manifest_to_profile(build_manifest({"entity_type": "startup", "registered_users": 5000}))
    assert profile["is_significant_data_fiduciary"] is False
    assert profile["processes_children_data"] is False
    assert profile["is_third_schedule_class"] is False
    assert profile["eu_roles"] == []


def test_profile_drives_applicability_gate():
    sdf_rule = {"id": "DPDP-SEC10-SDF-001",
                "applicability": {"scope": "significant_data_fiduciary_only"}}
    # typical startup → SDF rule NOT applicable
    startup = manifest_to_profile(build_manifest({"notified_as_sdf": False}))
    ok, _ = resolve_applicability(sdf_rule, startup)
    assert ok is False
    # notified SDF → applicable
    sdf = manifest_to_profile(build_manifest({"notified_as_sdf": True}))
    ok, _ = resolve_applicability(sdf_rule, sdf)
    assert ok is True


def test_validate_answers_reports_missing_required():
    missing = validate_answers({"entity_type": "startup"})
    assert "has_privacy_notice" in missing
    assert "grievance_email" not in missing  # optional


def test_questionnaire_ids_unique_and_complete():
    qs = get_questionnaire()
    ids = [q["id"] for q in qs]
    assert len(ids) == len(set(ids))
    assert set(ids) == QUESTION_IDS


# ── EU AI Act manifest fields (audit fix: eu_roles no longer hardcoded []) ──────

def test_eu_roles_empty_without_ai_or_eu_nexus():
    assert manifest_to_profile(build_manifest({"has_ai_system": False}))["eu_roles"] == []
    # AI system but no EU nexus -> no EU roles (never over-flag a non-EU entity)
    assert manifest_to_profile(build_manifest(
        {"has_ai_system": True, "eu_role": "provider", "provides_to_eu": False}))["eu_roles"] == []


def test_eu_provider_role_mapped_when_eu_nexus():
    p = manifest_to_profile(build_manifest(
        {"has_ai_system": True, "eu_role": "provider", "provides_to_eu": True}))
    assert p["eu_roles"] == ["eu_provider"]


def test_eu_gpai_provider_and_open_source_flag():
    p = manifest_to_profile(build_manifest(
        {"has_ai_system": True, "eu_role": "gpai_provider", "provides_to_eu": True, "is_open_source": True}))
    assert p["eu_roles"] == ["eu_gpai_provider"] and p["is_open_source"] is True


# ── Static questionnaire shipped to the landing page must not drift ────────────

def test_static_questionnaire_json_matches_source():
    """`landing-page` renders the questionnaire from a bundled JSON copy so the
    free tool does not block on a cold backend. Regenerate with:
        python scripts/export_questionnaire.py
    """
    import json
    from pathlib import Path

    static = Path(__file__).resolve().parents[1] / "landing-page/app/readiness/questionnaire.json"
    assert static.exists(), f"missing {static}; run scripts/export_questionnaire.py"
    assert json.loads(static.read_text())["questions"] == get_questionnaire()
