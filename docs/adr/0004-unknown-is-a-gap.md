# ADR 0004 — Unknown is a gap; never fabricate readiness

## Status

Accepted (2026-06-26). Enforced in `compliance/readiness.py`, `compliance/ropa.py`,
`agent/evaluators/file_presence.py`, `agent/evaluators/schema_validate.py`.

## Context

A compliance tool has a standing temptation: when it cannot determine something, round in the
client's favour. Every rounding is individually defensible and the aggregate is a lie. The
earlier engine did this in four places:

- `schema_validate.py` returned coverage `1.0` whenever a schema parsed, even with zero risks
  recorded.
- `techdoc_coverage.py` awarded 0.7 for a file merely existing — an empty `{}` model card
  passed EU AI Act Art. 11.
- `file_presence.py` accepted any non-empty value, so `{"provenance": "n/a"}` satisfied
  Art. 10 data-governance.
- The questionnaire treated an unanswered question as benign.

The compound effect: a client with correctly-named files full of placeholder text scored
near 100%. That is not a scoring bug. It is the product actively manufacturing false comfort,
which is precisely the harm a regulator penalises.

## Decision

**Absence of evidence is never evidence of readiness.** Concretely:

- An unanswered question counts as a **gap**, never as a pass. There is no "unknown" bucket
  that quietly rounds up.
- Placeholder values (`TODO`, `changeme`, `n/a`, whitespace) are treated as **missing**, with
  optional typed validation (email / ISO date / URL / min-length) per field.
- Coverage is measured by substantive field population, not by "the file parsed".
- Existence of a document earns nothing on its own.
- In the ROPA, anything unsourced is stamped `UNKNOWN`, listed in `unknowns` with how to fill
  it, and drags `completeness` below 100 — a register can never report itself complete while
  a column is unknown ([[0007-deterministic-records]]).

The rule generalises: **when the honest answer is "we cannot tell", say that.** It is why
`_changed_fields_by_hash` returns nothing rather than guessing when there is no baseline
([[0009-artefact-provenance-and-staleness]]), and why an unstamped artefact is reported as
`unstamped` rather than passed.

## Consequences

- **Positive.** Scores are trustworthy in the only direction that matters: we under-claim,
  never over-claim.
- **Positive.** The gap list doubles as a work list. "Unknown" tells the client exactly what
  only they can supply.
- **Negative — and significant.** Day-one scores are low, often 10-30%. This is a real
  commercial cost: a demo that opens with a bad number is a harder demo.
- **Mitigation, not dilution.** We answer the low score with the artefact generator and the
  collector — help the client *close* gaps rather than help the number look better.
- **Negative.** More client questions ("why did I fail when I have a policy?"). The answer —
  we could not verify it — is correct but costs support time.

## Alternatives considered

- **Partial credit for unknowns.** Rejected: it is the original bug with better manners.
- **Two scores, optimistic and conservative.** Rejected: clients quote the optimistic one and
  we have shipped the lie with a disclaimer attached.
- **Exclude unknowns from the denominator.** Rejected: a client who answers nothing would
  score 100%, which is the exact inversion of the truth.

## Related

[[0001-readiness-not-compliance]] · [[0003-applicability-gating]] ·
[[0007-deterministic-records]] · [[0009-artefact-provenance-and-staleness]]
