"""
Rulepack Schema v2 — field definitions + validator.

This module defines the v2 rulepack contract mandated by the legal-grounding and
legal-correctness appendices, and validates rulepacks against it. It is intentionally
dependency-light (stdlib only) so it can run inside the PyInstaller-compiled agent and
stay compatible with the open `complykit` rulepack format (v2 only ADDS fields; older
consumers ignore unknown keys).

What v2 requires, and WHY:

Pack level
- ``schema_version: 2``           — lets loaders branch on format.
- ``current_as_of``               — honesty: when was this pack's legal content current.
- ``legal_review_status``         — structural professional-review gate (pending|in_review|reviewed).
- ``legal_review_note``           — non-dismissable "pending legal review / not legal advice" note.
- ``reference_doc``               — points back at the grounded source-of-truth.

Per rule
- ``applicability``               — WHO the obligation binds (so the engine never flags a
                                     non-SDF startup for SDF-only duties). Addendum §2.
- ``act_citation`` / ``rule_citation`` — DUAL-LAYER citations. The substantive obligation
                                     (Act) and its operational mechanics (Rule) often live in
                                     different instruments; cite both where applicable. At
                                     least one is mandatory. Addendum §1.
- ``source_url``                  — a real, verifiable link for the citation. Grounding §1.
- ``status``                      — in_force | phased_not_yet_in_force | interpretation_uncertain.
- ``enforcement_date``            — when the obligation becomes enforceable (or null if live now).
- ``date_status``                 — in_force | phased_confirmed | provisional_pending_amendment
                                     (EU dates are mid-amendment; never present as fixed). Addendum §3.
- ``verification``                — primary_source_verified | secondary_source_only |
                                     interpretation_uncertain, so output can visually distinguish
                                     rock-solid findings from ones needing a lawyer's eye. Liability §3.

The validator is non-fatal by default (returns issues; callers decide). `strict=True`
raises so CI / pack authoring can hard-fail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

SCHEMA_VERSION = 2

# ── Allowed enum values ──────────────────────────────────────────────────────

APPLICABILITY_SCOPES = {
    # DPDP (India)
    "all_data_fiduciaries",
    "significant_data_fiduciary_only",
    "third_schedule_class_only",
    "consent_manager_only",
    "child_data_processing_only",
    "disability_guardian_only",
    "state_instrumentality_only",
    # EU AI Act roles (Art. 3)
    "eu_provider",
    "eu_deployer",
    "eu_importer",
    "eu_distributor",
    "eu_gpai_provider",
    "eu_gpai_downstream",
    "all_ai_actors",
}

STATUS_VALUES = {
    "in_force",
    "phased_not_yet_in_force",
    "interpretation_uncertain",
}

DATE_STATUS_VALUES = {
    "in_force",
    "phased_confirmed",
    "provisional_pending_amendment",
}

VERIFICATION_VALUES = {
    "primary_source_verified",
    "secondary_source_only",
    "interpretation_uncertain",
}

LEGAL_REVIEW_STATUS_VALUES = {
    "pending",
    "in_review",
    "reviewed",
}

# Fields every rule must carry under schema v2 (beyond the legacy execution fields).
REQUIRED_RULE_FIELDS = (
    "applicability",
    "source_url",
    "status",
    "enforcement_date",  # key required; value may be null when status == in_force
    "date_status",
    "verification",
)

# Pack-level fields required under schema v2.
REQUIRED_PACK_FIELDS = (
    "schema_version",
    "current_as_of",
    "legal_review_status",
    "legal_review_note",
)


class RulepackValidationError(ValueError):
    """Raised by :func:`assert_valid` when a pack fails v2 validation in strict mode."""


@dataclass
class ValidationResult:
    pack_id: str
    pack_errors: List[str] = field(default_factory=list)
    rule_errors: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.pack_errors and not self.rule_errors

    def summary(self) -> str:
        if self.ok:
            return f"rulepack '{self.pack_id}' is schema-v2 valid"
        lines = [f"rulepack '{self.pack_id}' has schema-v2 issues:"]
        for err in self.pack_errors:
            lines.append(f"  [pack] {err}")
        for rule_id, errs in self.rule_errors.items():
            for err in errs:
                lines.append(f"  [{rule_id}] {err}")
        return "\n".join(lines)


def _looks_like_url(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def validate_applicability(block: Any) -> List[str]:
    """Validate a rule's ``applicability`` block. Returns a list of issue strings."""
    issues: List[str] = []
    if not isinstance(block, dict):
        return ["applicability must be a mapping with at least a 'scope' field"]
    scope = block.get("scope")
    if not scope:
        issues.append("applicability.scope is required")
    elif scope not in APPLICABILITY_SCOPES:
        issues.append(
            f"applicability.scope '{scope}' is not one of {sorted(APPLICABILITY_SCOPES)}"
        )
    return issues


def validate_rule(rule: Dict[str, Any]) -> List[str]:
    """Validate a single rule dict against schema v2. Returns issue strings (empty == ok)."""
    issues: List[str] = []

    # Legacy execution contract still required.
    if not rule.get("id"):
        issues.append("missing 'id'")
    if not rule.get("evaluator"):
        issues.append("missing 'evaluator'")

    # v2 grounding/correctness fields.
    for f in REQUIRED_RULE_FIELDS:
        if f not in rule:
            issues.append(f"missing required v2 field '{f}'")

    # Dual-layer citation: at least one of act_citation / rule_citation must be present.
    if not rule.get("act_citation") and not rule.get("rule_citation"):
        issues.append("must carry at least one of 'act_citation' or 'rule_citation'")

    if "applicability" in rule:
        issues.extend(validate_applicability(rule["applicability"]))

    if "source_url" in rule and not _looks_like_url(rule["source_url"]):
        issues.append("source_url must be a http(s) URL")

    status = rule.get("status")
    if status is not None and status not in STATUS_VALUES:
        issues.append(f"status '{status}' not in {sorted(STATUS_VALUES)}")

    date_status = rule.get("date_status")
    if date_status is not None and date_status not in DATE_STATUS_VALUES:
        issues.append(f"date_status '{date_status}' not in {sorted(DATE_STATUS_VALUES)}")

    verification = rule.get("verification")
    if verification is not None and verification not in VERIFICATION_VALUES:
        issues.append(f"verification '{verification}' not in {sorted(VERIFICATION_VALUES)}")

    # enforcement_date may be null ONLY when the obligation is already in force.
    if "enforcement_date" in rule:
        ed = rule["enforcement_date"]
        if ed is None and status != "in_force":
            issues.append(
                "enforcement_date is null but status is not 'in_force' "
                "(a not-yet-live obligation needs a date)"
            )

    return issues


def validate_pack(pack: Dict[str, Any]) -> ValidationResult:
    """Validate a whole rulepack dict. Never raises; returns a :class:`ValidationResult`."""
    pack_id = str(pack.get("pack_id", "<unknown>"))
    result = ValidationResult(pack_id=pack_id)

    for f in REQUIRED_PACK_FIELDS:
        if f not in pack:
            result.pack_errors.append(f"missing required pack field '{f}'")

    if pack.get("schema_version") not in (None, SCHEMA_VERSION):
        result.pack_errors.append(
            f"schema_version must be {SCHEMA_VERSION} (got {pack.get('schema_version')!r})"
        )

    lrs = pack.get("legal_review_status")
    if lrs is not None and lrs not in LEGAL_REVIEW_STATUS_VALUES:
        result.pack_errors.append(
            f"legal_review_status '{lrs}' not in {sorted(LEGAL_REVIEW_STATUS_VALUES)}"
        )

    rules = pack.get("rules")
    if not isinstance(rules, list) or not rules:
        result.pack_errors.append("pack has no 'rules' list")
        return result

    for idx, rule in enumerate(rules, start=1):
        rule_id = str(rule.get("id", f"rule_{idx}"))
        issues = validate_rule(rule)
        if issues:
            result.rule_errors[rule_id] = issues

    return result


def assert_valid(pack: Dict[str, Any]) -> ValidationResult:
    """Validate and raise :class:`RulepackValidationError` if the pack is not v2-valid."""
    result = validate_pack(pack)
    if not result.ok:
        raise RulepackValidationError(result.summary())
    return result
