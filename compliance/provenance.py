"""Artefact provenance and staleness — "does this document still reflect the current law?"

Generating a compliance artefact is the easy half. The hard half is that the law moves, and a
document generated last quarter quietly stops being true. A register that *looks* current but
was built against a superseded rule is worse than no register: it manufactures false comfort,
which is exactly the failure mode a regulator punishes.

So every generated artefact is stamped with the rules it was built from, fingerprinted over
only the **legally material** fields. Later, ``assess_freshness()`` re-derives those
fingerprints from the current pack and reports one of three states:

  ``fresh``   nothing the artefact depends on has moved.
  ``review``  the pack moved, but not in a way that touches this artefact.
  ``stale``   a rule it depends on changed or vanished, or a new rule landed inside a domain
              this artefact claims to cover.

Cosmetic edits (a reworded internal title) deliberately do NOT change a fingerprint — a
staleness signal that cries wolf gets ignored, and an ignored signal is no signal.

This closes the loop with ``compliance/regwatch.py``: the watcher detects that a *source*
changed, and this module decides which *artefacts* that invalidates. Pure, no I/O.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from compliance.domains import DOMAINS

# The fields whose change is a change in the legal position. Everything else — internal
# titles, editorial notes, ordering — is presentation and must not trigger a false alarm.
LEGALLY_MATERIAL_FIELDS = (
    "id",
    "clause",
    "act_citation",
    "rule_citation",
    "source_url",
    "status",
    "enforcement_date",
    "date_status",
    "requirement",
    "description",
    "applicability",
    "verification",
)

_ACTIONS = {
    "rule_changed": "Re-generate this artefact and re-read the changed rule — the legal "
                    "position it was written against has moved.",
    "rule_removed": "A rule this artefact was built from is no longer in the pack. "
                    "Re-generate and confirm the obligation still exists.",
    "new_rule_in_covered_domain": "A new rule landed in a domain this artefact claims to "
                                  "cover. Re-generate so the artefact reflects it.",
    "pack_version_changed": "The rulepack version moved but none of this artefact's rules "
                            "changed. Re-generation is optional; a spot-check is prudent.",
    "pack_mismatch": "This artefact was built against a different rulepack. Compare against "
                     "the pack it was generated from, or re-generate against this one.",
}

# domain number -> the rules that evidence it (mirrors compliance/domains.py).
_DOMAIN_RULES = {d["number"]: set(d["rule_ids"]) for d in DOMAINS}


def _material(rule: Dict[str, Any]) -> Dict[str, Any]:
    return {k: rule.get(k) for k in LEGALLY_MATERIAL_FIELDS if rule.get(k) is not None}


def _hash(value: Any) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def rule_fingerprint(rule: Dict[str, Any]) -> str:
    """Stable hash over a rule's legally material fields only. Key order is irrelevant."""
    return _hash(_material(rule or {}))


def field_fingerprints(rule: Dict[str, Any]) -> Dict[str, str]:
    """Per-field hashes, so a later comparison can name *which* field moved.

    Hashes rather than values: the stamp travels with the artefact and must not become a
    partial copy of the rulepack (or of any legal text) sitting in the database.
    """
    return {k: _hash(v) for k, v in _material(rule or {}).items()}


def changed_fields(before: Dict[str, Any], after: Dict[str, Any]) -> List[str]:
    """Which legally material fields differ between two versions of the same rule."""
    a, b = _material(before or {}), _material(after or {})
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def _rules_by_id(pack: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {r["id"]: r for r in (pack.get("rules") or []) if r.get("id")}


def build_provenance(
    pack: Dict[str, Any],
    rule_ids: List[str],
    domains: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Stamp what an artefact was built from: the pack, and each depended-on rule's fingerprint.

    ``domains`` records the DPDPA domains the artefact claims to cover, so a *new* rule
    arriving in one of them can later be recognised as invalidating.
    """
    by_id = _rules_by_id(pack or {})
    wanted = list(dict.fromkeys(rule_ids or []))
    covered = sorted(domains) if domains else []
    return {
        "pack_id": (pack or {}).get("pack_id"),
        "pack_version": (pack or {}).get("pack_version") or (pack or {}).get("version"),
        "rules": {rid: {"fingerprint": rule_fingerprint(by_id[rid]),
                        "fields": field_fingerprints(by_id[rid])}
                  for rid in wanted if rid in by_id},
        "missing_rule_ids": [rid for rid in wanted if rid not in by_id],
        "domains": covered,
        # Which rules each covered domain contained AT STAMPING TIME. Without this baseline
        # "a new rule appeared in a covered domain" is uncomputable, and every domain rule the
        # artefact did not directly cite would read as new — a permanent false alarm.
        "domain_rules": {str(n): sorted(rid for rid in _DOMAIN_RULES.get(n, set())
                                        if rid in by_id)
                         for n in covered},
    }


def assess_freshness(stamp: Dict[str, Any], current_pack: Dict[str, Any]) -> Dict[str, Any]:
    """Re-derive the stamp against the current pack and classify the artefact.

    ``stale`` is reserved for changes that actually touch this artefact. A pack bump that
    leaves its rules alone is ``review`` — flagging that as stale would train users to ignore
    the flag.
    """
    stamp = stamp or {}
    by_id = _rules_by_id(current_pack or {})
    reasons: List[Dict[str, Any]] = []
    invalidating = False

    if stamp.get("pack_id") and current_pack.get("pack_id") != stamp.get("pack_id"):
        reasons.append({"kind": "pack_mismatch",
                        "expected": stamp.get("pack_id"),
                        "found": current_pack.get("pack_id"),
                        "action": _ACTIONS["pack_mismatch"]})

    for rule_id, recorded in (stamp.get("rules") or {}).items():
        rule = by_id.get(rule_id)
        if rule is None:
            invalidating = True
            reasons.append({"kind": "rule_removed", "rule_id": rule_id,
                            "action": _ACTIONS["rule_removed"]})
            continue
        if rule_fingerprint(rule) != recorded.get("fingerprint"):
            invalidating = True
            reasons.append({"kind": "rule_changed", "rule_id": rule_id,
                            "fields": _changed_fields_by_hash(
                                recorded.get("fields") or {}, field_fingerprints(rule)),
                            "action": _ACTIONS["rule_changed"]})

    # A domain rule is "new" only relative to what that domain held when the stamp was taken.
    # A stamp with no baseline (pre-dating this field) cannot answer the question, so it stays
    # silent rather than guessing — a false stale flag trains people to ignore the real ones.
    baseline = stamp.get("domain_rules") or {}
    for number in stamp.get("domains") or []:
        if str(number) not in baseline:
            continue
        known_then = set(baseline[str(number)])
        for rule_id in sorted(_DOMAIN_RULES.get(number, set())):
            if rule_id in by_id and rule_id not in known_then:
                invalidating = True
                reasons.append({"kind": "new_rule_in_covered_domain", "rule_id": rule_id,
                                "domain": number,
                                "action": _ACTIONS["new_rule_in_covered_domain"]})

    pack_version = (current_pack or {}).get("pack_version") or (current_pack or {}).get("version")
    if stamp.get("pack_version") and pack_version != stamp.get("pack_version"):
        reasons.append({"kind": "pack_version_changed",
                        "from": stamp.get("pack_version"), "to": pack_version,
                        "action": _ACTIONS["pack_version_changed"]})

    if invalidating:
        status = "stale"
    elif reasons:
        status = "review"
    else:
        status = "fresh"
    return {"status": status, "reasons": reasons,
            "pack_id": current_pack.get("pack_id"), "pack_version": pack_version}


def impacted_artefacts(
    affected_rule_ids: List[str],
    artefacts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Which stamped artefacts a set of changed rules invalidates.

    This is the join that closes the regulatory loop: ``compliance/regwatch.py`` detects that
    a legal source moved and names the rules it touches; this decides which documents the
    client is holding are now suspect.

    Two ways an artefact is hit:
      ``dependency``  it was built from one of the changed rules.
      ``domain``      it claims to cover a DPDPA domain the changed rule belongs to — a new or
                      altered obligation in that domain is still the artefact's problem, even
                      though it never cited that rule.
    An artefact with no provenance stamp is reported as ``unstamped``: we cannot prove it is
    unaffected, and silently passing it would be the same lie the stamp exists to prevent.
    """
    affected = set(affected_rule_ids or [])
    if not affected:
        return []
    domains_of_affected = {
        number for number, rule_ids in _DOMAIN_RULES.items() if affected & rule_ids
    }

    out: List[Dict[str, Any]] = []
    for artefact in artefacts or []:
        stamp = artefact.get("provenance")
        art_id = artefact.get("artefact_id")
        if not stamp:
            out.append({"artefact_id": art_id, "via": "unstamped", "rule_ids": sorted(affected),
                        "domains": [], "action": "This artefact carries no provenance stamp, so "
                                                 "we cannot tell whether the change affects it. "
                                                 "Re-generate it to get one."})
            continue

        direct = sorted(affected & set(stamp.get("rules") or {}))
        if direct:
            out.append({"artefact_id": art_id, "via": "dependency", "rule_ids": direct,
                        "domains": list(stamp.get("domains") or []),
                        "action": _ACTIONS["rule_changed"]})
            continue

        covered = sorted(set(stamp.get("domains") or []) & domains_of_affected)
        if covered:
            hit_rules = sorted(
                rid for rid in affected
                if any(rid in _DOMAIN_RULES.get(n, set()) for n in covered)
            )
            out.append({"artefact_id": art_id, "via": "domain", "rule_ids": hit_rules,
                        "domains": covered,
                        "action": _ACTIONS["new_rule_in_covered_domain"]})
    return out


def _changed_fields_by_hash(before: Dict[str, str], after: Dict[str, str]) -> List[str]:
    """Which fields moved, comparing stamped per-field hashes — no legal text needed."""
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
