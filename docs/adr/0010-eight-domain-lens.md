# ADR 0010 — Present DPDPA through the eight domains the market already reads

## Status

Accepted (2026-08-11). Implemented in `compliance/domains.py`; coverage enforced by
`tests/test_domains.py`.

## Context

Our rulepack is organised by statutory section: `DPDP-SEC5-NOTICE-001`,
`DPDP-SEC16-TRANSFER-001`. That is the right internal structure — it maps one-to-one to the
instrument and makes review by counsel tractable ([[0002-rulepack-schema-v2]]).

It is not how the market reads a compliance assessment. The gap-assessment deliverables Indian
enterprises and their consultants circulate present DPDPA as **eight domains**, and pin the
applicable domain numbers onto each stage of a product data-flow diagram:

1. Grounds of processing · 2. Notice · 3. Consent · 4. Data security measures ·
5. Children's data · 6. Significant Data Fiduciary obligations · 7. Data Principal rights ·
8. Cross-border transfer

A reviewer reads the picture and the register together: *at this stage domains 2 and 3 apply;
at that store, 4 and 8.* Handing that reviewer a list of section IDs makes them do a
translation they should not have to do, and makes our output look unlike the artefact they
already know how to review.

The risk in adopting the lens is real: a domain model maintained by hand drifts behind the
rulepack, and then we are shipping two inconsistent accounts of the same law.

## Decision

Model the eight domains in `compliance/domains.py` as a **view over the rulepack, never a
second source of truth** — and prove the relationship by test rather than assert it in a
comment.

- Each domain carries a number, title, act citation, summary, and the `rule_ids` that evidence
  it. A rule may back more than one domain (guardian consent is both consent and children's
  data).
- `domain_coverage(pack)` reports, against a loaded pack, both failure directions:
  **holes** (a domain with no backing rule in this pack) and **orphans**
  (`uncovered_rule_ids` — a rule no domain claims, meaning the model has drifted behind).
  `tests/test_domains.py` asserts zero orphans for every live DPDP pack, so adding a rule
  without placing it in a domain fails CI.
- `applicable_domains(answers)` gates 5, 6 and 8 on declared facts, reusing the logic of
  [[0003-applicability-gating]].
- `domains_for_row()` and `domains_for_node()` decide which domains attach to a ROPA row and
  to a DFD stage — the collection point carries notice and consent, a store carries security
  and (if abroad) cross-border, a processor carries security.
- The legend always lists **all eight**, marking the inapplicable ones "not applicable to your
  declared profile". Absence is a recorded decision, never a silent omission.

## Consequences

- **Positive.** Output lands in a format buyers, consultants and auditors already read, which
  removes an explanation step from every sales conversation.
- **Positive.** We record what was *ruled out* and why. The consulting deliverables we are
  matching generally do not.
- **Positive.** The domain becomes a useful unit elsewhere — notably the "new rule in a
  covered domain" signal in [[0009-artefact-provenance-and-staleness]].
- **Negative.** A hand-maintained mapping is a maintenance obligation. The orphan test makes
  drift loud rather than impossible.
- **Negative.** Some domain groupings are judgement calls. Placing retention, breach and
  processor contracts all under "data security measures" follows s.8's structure as general
  obligations of a Data Fiduciary, but a reviewer could reasonably split them. Flagged for
  legal review.
- **Negative.** DPDP-specific. The EU AI Act needs its own lens; this model does not stretch.

## Alternatives considered

- **Present raw section IDs only.** Rejected: correct and unreadable to the buyer.
- **Replace the section-based rulepack with domain-based rules.** Rejected: would break the
  one-to-one mapping to the instrument that makes legal review possible.
- **Hardcode the mapping in the rulepack YAML.** Rejected: couples presentation to the legal
  source of truth and would need re-review on every presentation change.

## Related

[[0002-rulepack-schema-v2]] · [[0003-applicability-gating]] ·
[[0011-diagram-derives-from-register]] · [[0009-artefact-provenance-and-staleness]]
