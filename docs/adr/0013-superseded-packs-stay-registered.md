# ADR 0013 — Superseded rulepacks stay registered, so past assessments stay reproducible

## Status

Accepted (2026-07-18). Visible in `rulepacks/` (`dpdp_india_extended_v1` retained alongside
`v2`, `euai_core_v1` alongside `v2`) and in each pack's `changelog` / `superseded_pack`.

## Context

When a rulepack is revised — a rule added, an enforcement date corrected, a scope narrowed —
the obvious move is to overwrite it. One file per jurisdiction, always current, nothing stale
to confuse anyone.

That makes every historical assessment unreproducible. A client scored 62% in June, acted on
that report, and shows it to an auditor in December. Re-running the assessment now yields a
different number against a different rule set, and there is no way to demonstrate that the
June report was correct *as at June*. The report becomes an unverifiable claim, which is
exactly what the evidence pack ([[0002-rulepack-schema-v2]]) exists to avoid.

It also destroys our own ability to answer "why did this change?" — the audit trail that
[[0008-human-gated-regwatch]] is built to produce ends at the current file.

## Decision

**Rulepack versions are immutable and additive.**

- A revision creates a **new pack file** with a new `pack_id` (`..._v2`) and a bumped
  `pack_version`. The prior pack file is **not** deleted and **stays registered** as a
  loadable pack.
- The new pack records `superseded_pack` and a dated `changelog` entry explaining what moved
  and why.
- Assessments and generated artefacts record the `pack_id` + `pack_version` they were produced
  against — the same stamp [[0009-artefact-provenance-and-staleness]] uses for staleness.
  Reproducibility and staleness are two reads of one record.
- Ordinary corrections bump `pack_version` within a pack; changes to the rule *set* create a
  new pack id.

## Consequences

- **Positive.** Any past assessment can be re-run against the exact pack that produced it.
  "Correct as at the law we had recorded on 18 July 2026" is a defensible statement.
- **Positive.** Rulepack evolution is legible: the changelog chain is the history of our
  reading of the law, which is a genuine asset in diligence.
- **Positive.** Enables honest staleness rather than silent drift.
- **Negative.** Pack files accumulate. Four live packs today; this grows with every revision
  and every jurisdiction.
- **Negative.** Pack selection becomes a real decision with a real failure mode. The ROPA
  stamps provenance against `dpdp_india_extended_v2` specifically, because the rules it cites
  do not all exist in core — a wrong default silently produces `missing_rule_ids`.
- **Negative.** Legal review has to be redone per pack version, and old packs carry old
  review status. A client on `v1` is on a pack reviewed at `v1`'s standard.

## Alternatives considered

- **Mutate one pack per jurisdiction, rely on git history.** Rejected: git history is not
  reachable from a running assessment, and a client cannot audit our repository.
- **Store a full copy of the pack inside every assessment record.** Reproducible, but bloats
  every record and duplicates legal text throughout the database — the same objection as
  storing rule text in provenance stamps.
- **Version rules individually rather than packs.** More precise and considerably more
  machinery. Pack-level versioning is the right granularity at current scale; revisit if
  rulepacks grow past a few hundred rules.

## Related

[[0002-rulepack-schema-v2]] · [[0008-human-gated-regwatch]] ·
[[0009-artefact-provenance-and-staleness]]
