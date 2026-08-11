# ADR 0002 — Rulepack schema v2: dual citations, applicability, dated enforcement

## Status

Accepted (2026-06-26). Implemented in `compliance/rulepack_schema.py`; all four live packs
(`dpdp_india_*`, `euai_*`) are v2.

## Context

Schema v1 rules were essentially `{id, title, check}`. That is enough to score something and
nowhere near enough to defend the score. Three failures showed up immediately:

- **No provenance.** A finding said "you fail DPDP s.8" with no pointer to the Act text, the
  corresponding Rule, or where either was read from. A reviewer could not verify it, and
  neither could we.
- **No temporal model.** DPDP obligations phase in across November 2025 → November 2026 →
  May 2027. Without an enforcement date per rule, everything reads as due now, which is the
  failure [[0001-readiness-not-compliance]] exists to prevent.
- **No applicability.** Rules fired at everyone. A three-person SaaS was told it had missed
  Significant-Data-Fiduciary duties it will never have.

The rulepack is also the company's principal durable asset. If it is not structured well
enough for a lawyer to review rule-by-rule, the legal review that unblocks the product cannot
happen efficiently.

## Decision

Adopt schema v2, validated by `compliance/rulepack_schema.py`. Every rule must carry:

| Field | Why it is mandatory |
|---|---|
| `act_citation` + `rule_citation` | The Act and the subordinate Rule are different instruments with different commencement. One citation cannot represent both. |
| `source_url` | The primary source the text was read from — also the unit the watcher monitors ([[0008-human-gated-regwatch]]). |
| `applicability` | `scope`, `threshold`, `exemption_ref` — drives the gate in [[0003-applicability-gating]]. |
| `status`, `enforcement_date`, `date_status` | Is this in force, and if not, when? `date_status` distinguishes a confirmed statutory date from a provisional reading. |
| `verification` | How the claim was verified (primary text, secondary source, pending) — surfaced as a badge so a reader can weigh it. |

Packs additionally carry `pack_version`, `legal_review_status`, `reviewer`, `reviewed_on`,
`changelog`, and `scope_exclusions` — the last so that a deliberate omission reads as a
recorded decision rather than a miss.

Superseded packs stay registered (`dpdp_india_extended_v1` alongside `v2`) so a past
assessment remains reproducible.

## Consequences

- **Positive.** Every finding carries its own evidence trail. This is what makes the evidence
  pack, the PDF and the ROPA defensible rather than assertive.
- **Positive.** Legal review becomes tractable: counsel reviews structured rows with source
  URLs, not prose.
- **Positive.** Enables artefact staleness ([[0009-artefact-provenance-and-staleness]]) —
  fingerprinting the legally material fields is only meaningful because those fields exist.
- **Negative.** Authoring a rule is materially more expensive. Coverage grows slower.
- **Negative.** Two citation fields invite drift between them; only review catches it.
- **Negative.** Pack retention means dead packs accumulate. Accepted for reproducibility.

## Alternatives considered

- **Keep v1, add citations as free text.** Rejected: unparseable, so neither the watcher nor
  the staleness engine could use it, and both are core.
- **One `citation` field.** Rejected: the Act and the Rules commence separately and can move
  independently. Collapsing them loses exactly the distinction that matters in 2026-27.
- **Model rules as executable code rather than data.** Rejected: a lawyer must be able to
  review a rule. YAML is reviewable; Python is not, by the reviewer who matters.

## Related

[[0001-readiness-not-compliance]] · [[0003-applicability-gating]] ·
[[0008-human-gated-regwatch]] · [[0009-artefact-provenance-and-staleness]]
