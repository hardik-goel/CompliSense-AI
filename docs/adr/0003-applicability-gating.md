# ADR 0003 — Gate rules on applicability; report NOT_APPLICABLE explicitly

## Status

Accepted (2026-06-26). Implemented in `compliance/applicability.py`, consumed by
`compliance/readiness.py`.

## Context

DPDP and the EU AI Act are both heavily conditional. Significant-Data-Fiduciary duties bind
only entities the Central Government has notified. Children's-data duties bind only those
processing children's data. Third-Schedule class retention binds only listed classes. EU AI
Act provider duties do not bind a pure deployer; the open-source exemption removes others.

Scoring every rule against every organisation produced two distinct harms:

- **False alarm.** A five-person startup was shown SDF obligations as gaps. The client either
  panics or — far more likely, and worse — learns that our findings are noise.
- **Silent omission.** Conversely, when we *did* skip a rule, the report simply did not
  mention it. A reader could not tell whether the rule had been assessed and passed, ruled
  out, or forgotten. All three look identical: absence.

## Decision

Applicability is a first-class outcome, not a filter.

- Each v2 rule declares `applicability: {scope, threshold, exemption_ref}`.
- `manifest_to_profile()` turns the Tier-0 answers into the profile the gate evaluates.
- A rule that does not apply is emitted as **`NOT_APPLICABLE`**, with the reason and the
  exemption reference — it is *not* dropped.
- `NOT_APPLICABLE` rules are excluded from the score denominator, so readiness is measured
  against the duties that actually bind this entity.
- Packs also carry `scope_exclusions` for whole areas assessed by nobody by default (e.g.
  Consent Manager First Schedule duties), surfaced as "out of scope for your profile".

## Consequences

- **Positive.** Scores become meaningful: 60% means 60% of *your* duties, not 60% of a list
  that includes duties for banks.
- **Positive.** Every omission is on the record as a decision. A reviewer can challenge the
  gate rather than wonder about the silence. This is the same instinct as
  [[0004-unknown-is-a-gap]] pointed at a different failure mode.
- **Negative.** The gate depends on self-declared facts. A client who wrongly answers "not an
  SDF" gets a score that excludes duties that in fact bind them. Mitigated by recording the
  declaration and surfacing it, never by silently second-guessing it.
- **Negative.** Two entities get non-comparable scores. Deliberate — cross-entity comparison
  was never a sound thing to offer.
- **Negative.** More report surface area: NOT_APPLICABLE rows lengthen the output.

## Alternatives considered

- **Filter non-applicable rules out silently.** Rejected: indistinguishable from an
  engineering gap, and it destroys the audit story.
- **Score everything, let the client ignore what does not apply.** Rejected: it makes the
  score meaningless and trains clients to dismiss findings.
- **Infer applicability from connectors instead of asking.** Rejected as the primary path:
  connector metadata cannot establish whether the Government has notified you as an SDF.
  Connectors *suggest*; the human confirms ([[0005-names-only-pii-inference]]).

## Related

[[0002-rulepack-schema-v2]] · [[0004-unknown-is-a-gap]] · [[0010-eight-domain-lens]]
