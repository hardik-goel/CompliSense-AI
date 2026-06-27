"""Map discovery signals to manifest answer *suggestions* (Phase 3.1).

Pure logic. A suggestion is a proposal the user accepts or rejects — it is never
auto-applied to the manifest. Mappings stay honest: infrastructure presence corroborates
a control but does not prove a *documented* process, so suggestions that imply
documentation are framed for confirmation, and weak signals are framed for review.

Only a subset of manifest fields can be corroborated from read-only AWS discovery; PII
categories and consent posture cannot be inferred from infrastructure and are left to the
self-declared questionnaire.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from connectors.base import DiscoveredSignal, Suggestion


def _index(signals: List[DiscoveredSignal]) -> Dict[str, DiscoveredSignal]:
    indexed: Dict[str, DiscoveredSignal] = {}
    for sig in signals or []:
        indexed[sig.key] = sig  # last write wins; discovery emits one per key
    return indexed


def _truthy(sig: Optional[DiscoveredSignal]) -> bool:
    return bool(sig and sig.value is True)


def signals_to_suggestions(signals: List[DiscoveredSignal]) -> List[Suggestion]:
    idx = _index(signals)
    suggestions: List[Suggestion] = []

    # 1. Storage location — we scanned AWS, so AWS is in use (high confidence).
    suggestions.append(Suggestion(
        manifest_field="storage_locations",
        suggested_value=["aws"],
        confidence="high",
        rationale="Discovery ran against a live AWS account, so AWS hosts at least some data/services.",
        action="confirm",
        evidence_signals=[k for k in ("has_data_stores", "rds_present", "primary_region") if k in idx],
    ))

    # 2. Security safeguards — corroborated by encryption + logging + access control.
    encryption = _truthy(idx.get("storage_encryption")) or _truthy(idx.get("rds_storage_encrypted")) \
        or _truthy(idx.get("encryption_keys_present"))
    logging_on = _truthy(idx.get("audit_logging_enabled"))
    access_control = _truthy(idx.get("public_access_blocked")) or _truthy(idx.get("mfa_enabled"))
    present = [name for name, ok in (("encryption", encryption), ("logging", logging_on),
                                     ("access-control", access_control)) if ok]
    missing = [name for name in ("encryption", "logging", "access-control") if name not in present]

    if encryption and logging_on and access_control:
        suggestions.append(Suggestion(
            manifest_field="has_security_safeguards",
            suggested_value=True,
            confidence="high",
            rationale="Observed encryption, audit logging, and access controls in AWS. "
                      "Confirm these are also documented.",
            action="confirm",
            evidence_signals=[k for k in ("storage_encryption", "rds_storage_encrypted",
                                          "encryption_keys_present", "audit_logging_enabled",
                                          "public_access_blocked", "mfa_enabled") if _truthy(idx.get(k))],
        ))
    elif present:
        suggestions.append(Suggestion(
            manifest_field="has_security_safeguards",
            suggested_value=False,
            confidence="medium",
            rationale=f"Partial controls observed ({', '.join(present)}); not yet evidenced: {', '.join(missing)}.",
            action="review",
            evidence_signals=[k for k in idx if k in (
                "storage_encryption", "rds_storage_encrypted", "encryption_keys_present",
                "audit_logging_enabled", "public_access_blocked", "mfa_enabled")],
        ))

    # 3. Retention — S3 lifecycle rules or AWS Backup plans hint at defined retention.
    if _truthy(idx.get("retention_lifecycle_present")) or _truthy(idx.get("backup_configured")):
        suggestions.append(Suggestion(
            manifest_field="retention_defined",
            suggested_value=True,
            confidence="medium",
            rationale="S3 lifecycle rules and/or AWS Backup plans suggest retention is configured. "
                      "Confirm periods are defined and documented.",
            action="review",
            evidence_signals=[k for k in ("retention_lifecycle_present", "backup_configured") if _truthy(idx.get(k))],
        ))

    # 4. Cross-border transfer — data/usage outside Indian regions warrants review.
    cross_border = _truthy(idx.get("data_outside_india"))
    region_sig = idx.get("primary_region")
    region_outside = bool(region_sig and region_sig.value not in ("ap-south-1", "ap-south-2"))
    if cross_border or region_outside:
        suggestions.append(Suggestion(
            manifest_field="cross_border_transfer",
            suggested_value=True,
            confidence="low",
            rationale="Resources or discovery region appear outside India — review whether personal "
                      "data is transferred cross-border.",
            action="review",
            evidence_signals=[k for k in ("data_outside_india", "primary_region") if k in idx],
        ))

    return suggestions
