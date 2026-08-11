"""Record of Processing Activities (ROPA) builder — deterministic, pure, no LLM.

A ROPA is a *register of facts*, not prose: which personal-data categories are processed,
for what purpose, whose data it is, where it lives, how long it is kept, on what legal
basis, and which processors touch it. Because it is a factual table, it is built
deterministically from confirmed inputs — never AI-drafted. An AI-drafted ROPA would be a
fabricated record, which is precisely the artefact you must not fabricate.

Inputs, in priority order per column:
  1. ``activities`` — processing activities the client declared (authoritative).
  2. ``flow_report`` — the names-only data-flow map from ``compliance/dataflow.py``
     (store -> personal-data categories, provider/region, cross-border flags).
  3. ``answers`` — the Tier-0 manifest answers.

Honesty stance, consistent with the readiness engine: **unknown is never dressed up as
complete.** Anything we cannot source is stamped ``UNKNOWN`` in the register, listed in
``unknowns`` with guidance on how to fill it, and drags ``completeness`` below 100.

Privacy stance, inherited from ``compliance/pii.py``: NAMES ONLY. The evidence surfaced for
an inferred row is the matched field *name* — never a personal-data value.

Legal stance: a ROPA is **not** a named obligation under the DPDP Act 2023 or the DPDP
Rules 2025. It is the standard evidence artefact that demonstrates the accountability those
provisions assume. Not legal advice; requires legal review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from compliance.domains import DOMAINS, applicable_domains, domains_for_row

UNKNOWN = "UNKNOWN — not declared"

# The columns a regulator-facing register is expected to carry. Completeness is measured
# against exactly these, per row.
ROPA_COLUMNS = ["purpose", "categories", "data_principals", "store",
                "retention", "legal_basis", "processors"]

# Rules whose evidence this register supports. It does not *close* them on its own.
SUPPORTS_RULES = [
    "DPDP-SEC5-NOTICE-001",         # itemised personal data in the notice (Rule 3)
    "DPDP-SEC7-LEGITIMATE-USE-001",  # legal basis per activity
    "DPDP-SEC8-OBLIGATIONS-003",    # retention & erasure periods
    "DPDP-SEC8-PROCESSOR-001",      # processors per activity
    "DPDP-SEC16-TRANSFER-001",      # cross-border placement
]

_HOW_TO_FILL = {
    "purpose": "State why this data is processed, in one line per activity "
               "(e.g. 'account creation and login'). Only you can supply this.",
    "categories": "List the personal-data categories held in this store. Run PII inference "
                  "on the field names, or declare them in the questionnaire.",
    "data_principals": "Say whose data this is — customers, employees, prospects, children.",
    "retention": "Define how long this data is kept and when it is erased "
                 "(DPDP s.8(7)-(8) / Rule 8).",
    "retention_period": "A retention schedule is declared but the period is not captured "
                        "here. Enter the actual period per activity.",
    "legal_basis": "Declare the basis: consent (s.6) or a legitimate use (s.7).",
    "processors": "List the third parties processing this data on your behalf, with their "
                  "data-processing agreements (s.8(2) / Rule 6(f)).",
    "processor_names": "A processor inventory is declared but the vendor names are not "
                       "captured here. Enter the processors touching this activity.",
}


@dataclass
class ProcessingActivity:
    """A processing activity the client declared. Authoritative over anything inferred."""

    activity_id: str
    purpose: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    data_principals: List[str] = field(default_factory=list)
    stores: List[str] = field(default_factory=list)
    retention: Optional[str] = None
    legal_basis: Optional[str] = None
    processors: List[str] = field(default_factory=list)


def _legal_basis_from_answers(answers: Dict[str, Any]) -> Optional[str]:
    mech = (answers.get("consent_mechanism") or "none").strip()
    if mech == "explicit_optin":
        return "consent"
    if mech == "pre_ticked_or_implied":
        return "consent (declared — mechanism may not satisfy DPDP s.6)"
    return None


def _retention_from_answers(answers: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """(value, unknown_field). Declared-but-unspecified is honest about the missing period."""
    if answers.get("retention_defined"):
        return "Declared — schedule exists; period not captured", "retention_period"
    return None, "retention"


def _processors_from_answers(answers: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    if answers.get("processors_listed"):
        return "Declared — inventory maintained; names not captured", "processor_names"
    return None, "processors"


def _store_meta(flow_report: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """store name -> {provider, region, in_india, categories, evidence_field_names}."""
    out: Dict[str, Dict[str, Any]] = {}
    for src in (flow_report or {}).get("sources", []) or []:
        evidence: List[str] = []
        for cat in src.get("categories", []) or []:
            evidence.extend(cat.get("matched_on", []) or [])
        out[src["name"]] = {
            "provider": src.get("provider"),
            "region": src.get("region"),
            "in_india": src.get("in_india", False),
            "categories": [c["category"] for c in src.get("categories", []) or []],
            "evidence_field_names": sorted(set(evidence)),
        }
    return out


def build_ropa(
    answers: Dict[str, Any],
    flow_report: Optional[Dict[str, Any]] = None,
    activities: Optional[List[ProcessingActivity]] = None,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a ROPA register from declared activities, inferred data flows and the manifest.

    Pure: no clock, no I/O. ``generated_at`` is caller-supplied so the output is reproducible.
    """
    answers = answers or {}
    meta = _store_meta(flow_report)
    rows: List[Dict[str, Any]] = []
    unknowns: List[Dict[str, Any]] = []
    fields_known = 0

    def _emit(row_id: str, store: Optional[str], provenance: str,
              act: Optional[ProcessingActivity]) -> None:
        nonlocal fields_known
        m = meta.get(store or "", {})
        missing: Dict[str, str] = {}   # column -> unknown field name

        purpose = (act.purpose if act else None) or None
        if not purpose:
            missing["purpose"] = "purpose"

        categories = list(act.categories) if act and act.categories else []
        if not categories:
            categories = list(m.get("categories") or []) or list(answers.get("pii_categories") or [])
        if not categories:
            missing["categories"] = "categories"

        principals = list(act.data_principals) if act and act.data_principals else []
        if not principals:
            missing["data_principals"] = "data_principals"

        if not store:
            missing["store"] = "store"

        retention = act.retention if act else None
        if not retention:
            retention, ret_unknown = _retention_from_answers(answers)
            if ret_unknown:
                missing["retention"] = ret_unknown

        basis = (act.legal_basis if act else None) or _legal_basis_from_answers(answers)
        if not basis:
            missing["legal_basis"] = "legal_basis"

        processors = list(act.processors) if act and act.processors else []
        processors_display: Any = processors
        if not processors:
            processors_display, proc_unknown = _processors_from_answers(answers)
            if proc_unknown:
                missing["processors"] = proc_unknown

        # Cross-border: the flow map is authoritative; fall back to the declared posture.
        region = m.get("region")
        if region is not None:
            cross_border = not m.get("in_india", False)
        else:
            cross_border = bool(answers.get("cross_border_transfer"))

        row = {
            "activity_id": row_id,
            "purpose": purpose or UNKNOWN,
            "categories": categories,
            "data_principals": principals or UNKNOWN,
            "store": store or UNKNOWN,
            "provider": m.get("provider"),
            "region": region,
            "cross_border": cross_border,
            "retention": retention or UNKNOWN,
            "legal_basis": basis or UNKNOWN,
            "processors": processors_display or UNKNOWN,
            "evidence_field_names": m.get("evidence_field_names", []),
            "provenance": provenance,
        }
        # The DPDPA domains a reviewer would pin to this stage of the flow.
        row["domains"] = domains_for_row(row, answers)
        rows.append(row)
        for column in ROPA_COLUMNS:
            if column in missing:
                unknowns.append({
                    "activity_id": row_id, "column": column, "field": missing[column],
                    "why": "Not supplied by a declared activity, the data-flow map, or the manifest.",
                    "how_to_fill": _HOW_TO_FILL.get(missing[column], ""),
                })
            else:
                fields_known += 1

    if activities:
        for act in activities:
            stores = act.stores or [None]
            for store in stores:
                _emit(act.activity_id, store, "declared", act)
    elif meta:
        for store in meta:
            _emit(store, store, "inferred", None)
    else:
        declared = list(answers.get("storage_locations") or [])
        for store in declared or [None]:
            _emit(store or "undeclared", store, "declared_manifest", None)

    total = len(rows) * len(ROPA_COLUMNS)
    percent = round(fields_known / total * 100) if total else 0

    cross_border_rows = [
        {"activity_id": r["activity_id"], "store": r["store"], "provider": r["provider"],
         "region": r["region"], "categories": r["categories"]}
        for r in rows if r["cross_border"]
    ]

    return {
        "generated_at": generated_at,
        "controller": {
            "entity_type": answers.get("entity_type"),
            "sector": answers.get("sector"),
            "offers_in_india": bool(answers.get("offers_in_india", False)),
            "is_significant_data_fiduciary": bool(answers.get("notified_as_sdf", False)),
            "processes_children_data": bool(answers.get("processes_children_data", False)),
            "grievance_contact": answers.get("grievance_email"),
        },
        "rows": rows,
        "cross_border": cross_border_rows,
        "has_cross_border": bool(cross_border_rows),
        "unknowns": unknowns,
        "completeness": {"fields_total": total, "fields_known": fields_known, "percent": percent},
        # The eight-domain lens buyers and auditors read compliance through. The legend always
        # carries all eight so a reader can see what was assessed AND what was ruled out.
        "domains": {
            "applicable": applicable_domains(answers),
            "legend": [{"number": d["number"], "domain_id": d["domain_id"],
                        "title": d["title"], "act_citation": d["act_citation"],
                        "summary": d["summary"]} for d in DOMAINS],
        },
        "supports_rules": list(SUPPORTS_RULES),
        "notes": {
            "status": "A Record of Processing Activities is not a named obligation under the "
                      "DPDP Act 2023 or the DPDP Rules 2025. It is the standard evidence "
                      "artefact demonstrating the accountability those provisions assume, and "
                      "is what auditors and enterprise buyers ask for first.",
            "privacy": "Inferred rows are derived from field NAMES only — never from personal-data "
                       "values. The evidence shown is the matched field name.",
            "disclaimer": "DRAFT — REQUIRES LEGAL REVIEW. Not legal advice and not a compliance "
                          "determination.",
        },
    }


def _cell(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else UNKNOWN
    return str(value)


def ropa_to_markdown(ropa: Dict[str, Any]) -> str:
    """Render the register as a Markdown document (the client-facing / exportable artefact)."""
    c = ropa.get("controller", {})
    lines: List[str] = [
        "# Record of Processing Activities (ROPA)",
        "",
        "> **DRAFT — REQUIRES LEGAL REVIEW.** Not legal advice and not a compliance "
        "determination. A ROPA is not a named obligation under the DPDP Act 2023 or the "
        "DPDP Rules 2025; it is the standard evidence artefact demonstrating accountability.",
        "",
        "## Data Fiduciary",
        "",
        f"- Entity type: {_cell(c.get('entity_type') or UNKNOWN)}",
        f"- Sector: {_cell(c.get('sector') or UNKNOWN)}",
        f"- Offers goods/services in India: {'yes' if c.get('offers_in_india') else 'no'}",
        f"- Significant Data Fiduciary: {'yes' if c.get('is_significant_data_fiduciary') else 'no'}",
        f"- Processes children's data: {'yes' if c.get('processes_children_data') else 'no'}",
        f"- Grievance contact: {_cell(c.get('grievance_contact') or UNKNOWN)}",
        "",
        "## Processing activities",
        "",
        "| Activity | Purpose | Store | Provider / region | Categories | Data principals "
        "| Retention | Legal basis | Processors | Cross-border | DPDPA domains | Source |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in ropa.get("rows", []):
        location = " / ".join(x for x in [r.get("provider"), r.get("region")] if x) or UNKNOWN
        lines.append(
            f"| {_cell(r['activity_id'])} | {_cell(r['purpose'])} | {_cell(r['store'])} "
            f"| {location} | {_cell(r['categories'])} | {_cell(r['data_principals'])} "
            f"| {_cell(r['retention'])} | {_cell(r['legal_basis'])} | {_cell(r['processors'])} "
            f"| {'yes' if r['cross_border'] else 'no'} | {_cell(r.get('domains') or [])} "
            f"| {_cell(r['provenance'])} |"
        )

    comp = ropa.get("completeness", {})
    lines += ["", f"**Completeness: {comp.get('percent', 0)}%** "
                  f"({comp.get('fields_known', 0)} of {comp.get('fields_total', 0)} register "
                  f"fields sourced from declared or inferred facts).", ""]

    unknowns = ropa.get("unknowns", [])
    if unknowns:
        lines += ["## What is still missing", "",
                  "Each item below is either stamped `" + UNKNOWN + "` in the register above, "
                  "or declared without the detail a register needs. The register is not "
                  "complete until they are filled.", ""]
        for u in unknowns:
            lines.append(f"- **{u['activity_id']} · {u['column']}** — {u['how_to_fill']}")
        lines.append("")

    if ropa.get("has_cross_border"):
        lines += ["## Cross-border placement", "",
                  "Personal data was mapped to stores outside India. Review against DPDP s.16 "
                  "and Rule 15 (transfers may be restricted by the Central Government).", ""]
        for cb in ropa.get("cross_border", []):
            lines.append(f"- `{cb['store']}` ({cb.get('provider') or 'unknown provider'} / "
                         f"{cb.get('region') or 'unknown region'}) — {_cell(cb['categories'])}")
        lines.append("")

    domains = ropa.get("domains") or {}
    if domains.get("legend"):
        applicable = set(domains.get("applicable") or [])
        lines += ["## DPDPA domains", "",
                  "The numbers in the register above are these domains. A domain marked "
                  "*not applicable* was ruled out by your declared facts — so its absence is a "
                  "decision on record, not an omission.", "",
                  "| # | Domain | Applies | Citation |", "|---|---|---|---|"]
        for d in domains["legend"]:
            applies = "yes" if d["number"] in applicable else "not applicable"
            lines.append(f"| {d['number']} | {d['title']} | {applies} | {d['act_citation']} |")
        lines.append("")

    lines += ["## Evidence basis", "",
              ropa.get("notes", {}).get("privacy", ""), "",
              "Supports (does not on its own close): " +
              ", ".join(ropa.get("supports_rules", [])), ""]
    return "\n".join(lines)
