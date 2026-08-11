"""The eight DPDPA domains — the lens the market already reads compliance through.

Bank and enterprise gap-assessment deliverables do not present DPDPA as a list of sections.
They present eight **domains**, and pin the applicable domain numbers onto each stage of a
product data-flow diagram. A reviewer then reads the picture and the register together:
"at this stage, domains 2 and 3 apply; at that store, 4 and 8."

This module is that lens. It is a *view over the rulepack*, never a second source of truth:
``domain_coverage()`` proves, against a loaded pack, that every rule lands in a domain and
reports both holes (a domain with no backing rule) and orphans (a rule no domain knows).
A domain model that silently drifts from the rules is worse than none, so the drift is a
test, not a comment.

Pure logic, no I/O. Readiness framing, not legal advice.
"""

from __future__ import annotations

from typing import Any, Dict, List

# number -> domain. `rule_ids` are the rules that evidence the domain; a rule may back more
# than one domain (guardian consent is both a consent and a children's-data control).
DOMAINS: List[Dict[str, Any]] = [
    {
        "number": 1, "domain_id": "grounds_of_processing",
        "title": "Grounds of processing personal data",
        "act_citation": "DPDP Act 2023, s.4 (processing only for a lawful purpose) with s.7 "
                        "(legitimate uses)",
        "summary": "Every processing activity rests on a lawful ground — consent, or a "
                   "listed legitimate use.",
        "rule_ids": ["DPDP-SEC7-LEGITIMATE-USE-001"],
    },
    {
        "number": 2, "domain_id": "notice",
        "title": "Notice",
        "act_citation": "DPDP Act 2023, s.5; DPDP Rules 2025, Rule 3",
        "summary": "An itemised, plain-language notice is given at or before the point of "
                   "collection.",
        "rule_ids": ["DPDP-SEC5-NOTICE-001"],
    },
    {
        "number": 3, "domain_id": "consent",
        "title": "Consent",
        "act_citation": "DPDP Act 2023, s.6 (and s.9 proviso for lawful guardians)",
        "summary": "Consent is free, specific, informed, unconditional and unambiguous, "
                   "recorded, and as easy to withdraw as to give.",
        "rule_ids": ["DPDP-SEC6-CONSENT-001", "DPDP-SEC9-GUARDIAN-001"],
    },
    {
        "number": 4, "domain_id": "data_security",
        "title": "Data security measures",
        "act_citation": "DPDP Act 2023, s.8 (general obligations of a Data Fiduciary); "
                        "DPDP Rules 2025, Rules 6-8",
        "summary": "Reasonable security safeguards, breach intimation, retention and erasure, "
                   "and processor contracts across every store that holds personal data.",
        "rule_ids": ["DPDP-SEC8-OBLIGATIONS-001", "DPDP-SEC8-OBLIGATIONS-002",
                     "DPDP-SEC8-OBLIGATIONS-003", "DPDP-SEC8-RETENTION-CLASS-001",
                     "DPDP-SEC8-PROCESSOR-001"],
    },
    {
        "number": 5, "domain_id": "children_data",
        "title": "Processing of personal data of children",
        "act_citation": "DPDP Act 2023, s.9; DPDP Rules 2025, Rule 10",
        "summary": "Verifiable parental consent, and the bans on tracking, behavioural "
                   "monitoring and targeted advertising to children.",
        "rule_ids": ["DPDP-SEC9-CHILDREN-001", "DPDP-SEC9-GUARDIAN-001"],
    },
    {
        "number": 6, "domain_id": "sdf_obligations",
        "title": "Obligations of a Significant Data Fiduciary",
        "act_citation": "DPDP Act 2023, s.10; DPDP Rules 2025, Rule 13",
        "summary": "DPO in India, independent data audit, periodic DPIA, and the additional "
                   "measures the Central Government notifies.",
        "rule_ids": ["DPDP-SEC10-SDF-001"],
    },
    {
        "number": 7, "domain_id": "data_principal_rights",
        "title": "Data Principal rights",
        "act_citation": "DPDP Act 2023, ss.11-14; DPDP Rules 2025, Rule 14",
        "summary": "Access, correction and erasure, grievance redressal, and nomination — "
                   "each with a published route and a response window.",
        "rule_ids": ["DPDP-SEC11-ACCESS-001", "DPDP-SEC12-CORRECTION-001",
                     "DPDP-SEC13-GRIEVANCE-001", "DPDP-SEC14-NOMINATION-001"],
    },
    {
        "number": 8, "domain_id": "cross_border_transfer",
        "title": "Cross-border data transfer",
        "act_citation": "DPDP Act 2023, s.16; DPDP Rules 2025, Rule 15",
        "summary": "Transfers outside India are permitted subject to restrictions the Central "
                   "Government may notify — so placement must be known and documented.",
        "rule_ids": ["DPDP-SEC16-TRANSFER-001"],
    },
]

_BY_NUMBER = {d["number"]: d for d in DOMAINS}
_BY_ID = {d["domain_id"]: d for d in DOMAINS}

# Domains gated on a manifest fact. Everything else applies to every Data Fiduciary.
_CONDITIONAL = {
    5: "processes_children_data",
    6: "notified_as_sdf",
    8: "cross_border_transfer",
}


def domain_by_number(number: int) -> Dict[str, Any]:
    if number not in _BY_NUMBER:
        raise KeyError(f"No DPDPA domain numbered {number}")
    return _BY_NUMBER[number]


def domain_by_id(domain_id: str) -> Dict[str, Any]:
    if domain_id not in _BY_ID:
        raise KeyError(f"No DPDPA domain {domain_id!r}")
    return _BY_ID[domain_id]


def domain_coverage(pack: Dict[str, Any]) -> Dict[str, Any]:
    """Prove the domain model against a loaded rulepack.

    ``by_domain``            domain_id -> the pack's rules backing it
    ``domains_without_rules`` domains this pack cannot evidence (a coverage hole)
    ``uncovered_rule_ids``    rules no domain claims (the model has drifted behind the pack)
    """
    pack_rule_ids = {r.get("id") for r in (pack.get("rules") or []) if r.get("id")}
    by_domain: Dict[str, List[str]] = {}
    claimed: set = set()
    for d in DOMAINS:
        present = sorted(rid for rid in d["rule_ids"] if rid in pack_rule_ids)
        by_domain[d["domain_id"]] = present
        claimed |= set(d["rule_ids"])
    return {
        "pack_id": pack.get("pack_id"),
        "by_domain": by_domain,
        "domains_without_rules": sorted(k for k, v in by_domain.items() if not v),
        "uncovered_rule_ids": sorted(pack_rule_ids - claimed),
    }


def applicable_domains(answers: Dict[str, Any]) -> List[int]:
    """Domain numbers that apply to this Data Fiduciary, given its declared facts."""
    answers = answers or {}
    return sorted(
        d["number"] for d in DOMAINS
        if d["number"] not in _CONDITIONAL or bool(answers.get(_CONDITIONAL[d["number"]]))
    )


def _always_on(answers: Dict[str, Any]) -> List[int]:
    """Domains that ride along on every stage once they apply to the entity at all."""
    return [6] if (answers or {}).get("notified_as_sdf") else []


def domains_for_row(row: Dict[str, Any], answers: Dict[str, Any]) -> List[int]:
    """Domains that apply to one ROPA row (an activity landing in one store).

    A row is a *holding* of personal data, so it carries the ground it rests on, the security
    obligations over the store, and the rights exercisable against it — but not notice, which
    attaches to the point of collection rather than the store.
    """
    answers = answers or {}
    nums = {1, 4, 7} | set(_always_on(answers))
    if row.get("legal_basis") and str(row["legal_basis"]).startswith("consent"):
        nums.add(3)
    categories = row.get("categories") or []
    if "children_data" in categories or answers.get("processes_children_data"):
        nums.add(5)
    if row.get("cross_border"):
        nums.add(8)
    return sorted(nums)


def domains_for_node(node_kind: str, node: Dict[str, Any], answers: Dict[str, Any]) -> List[int]:
    """Domains that apply at one DFD stage. This is what gets badged onto the diagram."""
    answers = answers or {}
    node = node or {}
    nums = set(_always_on(answers))

    if node_kind == "principal":
        # The point of collection: the ground, the notice and the consent are all taken here.
        # Domain 3 is badged whether or not a mechanism is declared — a missing consent
        # mechanism is a gap *within* the domain, not a reason to drop the domain.
        nums |= {1, 2, 3}
    elif node_kind == "activity":
        nums |= {1, 7}
        if answers.get("processes_children_data"):
            nums.add(5)
    elif node_kind == "store":
        nums |= {4, 7}
        if node.get("outside_india"):
            nums.add(8)
        if answers.get("processes_children_data"):
            nums.add(5)
    elif node_kind == "processor":
        nums.add(4)
        if node.get("outside_india"):
            nums.add(8)

    return sorted(nums)
