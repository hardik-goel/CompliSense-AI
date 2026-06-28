"""
Applicability gating for the compliance engine.

The same law says different things to different entities. An obligation that binds a
Significant Data Fiduciary (DPIA, audit, in-India DPO) must NOT be flagged as a gap for a
5-person startup that is not an SDF. Likewise an EU high-risk *provider* obligation must
not be loaded onto a startup that merely *deploys* third-party AI.

This module resolves a rule's ``applicability.scope`` against an **entity profile** (the
facts captured by the Tier-0 manifest in Phase 1). A non-applicable rule is reported as
``NOT_APPLICABLE`` — never as a failure.

Backward-compatibility contract:
- ``profile is None``  → gating is INACTIVE; every rule is applicable (preserves the
  pre-gating scan behaviour until a manifest provides a profile).
- ``profile`` provided → special scopes are gated on explicit profile flags. A flag that
  is missing is treated as False (i.e. the special obligation does not apply) so we never
  over-flag the ICP. Universal scopes (``all_data_fiduciaries`` / ``all_ai_actors``) are
  always applicable.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

# Scopes that always apply to anyone the pack targets.
UNIVERSAL_SCOPES = {"all_data_fiduciaries", "all_ai_actors"}

# Special scope -> the profile predicate that must be true for the rule to apply.
# DPDP scopes map to boolean flags; EU role scopes map to membership in profile["eu_roles"].
_BOOL_FLAG_FOR_SCOPE = {
    "significant_data_fiduciary_only": "is_significant_data_fiduciary",
    "child_data_processing_only": "processes_children_data",
    "third_schedule_class_only": "is_third_schedule_class",
    "consent_manager_only": "is_consent_manager",
    "state_instrumentality_only": "is_state_instrumentality",
}

_EU_ROLE_SCOPES = {
    "eu_provider",
    "eu_deployer",
    "eu_importer",
    "eu_distributor",
    "eu_gpai_provider",
    "eu_gpai_downstream",
}


def default_profile() -> Dict[str, Any]:
    """A conservative startup profile: not an SDF, no children's data, EU deployer only.

    The Phase-1 manifest replaces this with the user's declared facts. Used when a caller
    wants gating active but has no manifest yet.
    """
    return {
        "is_significant_data_fiduciary": False,
        "processes_children_data": False,
        "is_third_schedule_class": False,
        "is_consent_manager": False,
        "is_state_instrumentality": False,
        "eu_roles": ["eu_deployer"],
    }


def resolve_applicability(
    rule: Dict[str, Any], profile: Optional[Dict[str, Any]]
) -> Tuple[bool, str]:
    """Return ``(is_applicable, reason)`` for a rule under the given entity profile."""
    block = rule.get("applicability")
    if not isinstance(block, dict) or not block.get("scope"):
        # Legacy / unscoped rule — apply it (nothing to gate on).
        return True, "no applicability scope declared; applied by default"

    scope = block["scope"]

    if profile is None:
        return True, "applicability gating inactive (no entity profile provided)"

    # Open-source carve-out: a rule may declare `open_source_exempt: true`. When the entity
    # is open-source, that obligation does not apply. (Which EU rules carry this exemption is
    # subject to legal review — see LEGAL_REVIEW_NEEDED.md.)
    if block.get("open_source_exempt") and bool(profile.get("is_open_source")):
        return False, f"scope '{scope}' does not apply: open-source exemption (profile.is_open_source)"

    if scope in UNIVERSAL_SCOPES:
        return True, f"scope '{scope}' applies to all in-scope entities"

    if scope in _BOOL_FLAG_FOR_SCOPE:
        flag = _BOOL_FLAG_FOR_SCOPE[scope]
        if bool(profile.get(flag)):
            return True, f"profile.{flag} is true → scope '{scope}' applies"
        return False, (
            f"scope '{scope}' does not apply: profile.{flag} is not set. "
            f"{block.get('threshold') or ''}".strip()
        )

    if scope in _EU_ROLE_SCOPES:
        roles = profile.get("eu_roles") or []
        if scope in roles:
            return True, f"profile.eu_roles includes '{scope}'"
        return False, (
            f"scope '{scope}' does not apply: entity has not declared the "
            f"'{scope}' role (declared roles: {roles or 'none'}). "
            f"{block.get('threshold') or ''}".strip()
        )

    # Unknown scope — fail safe by applying it and letting validation surface the issue.
    return True, f"unknown scope '{scope}'; applied by default"
