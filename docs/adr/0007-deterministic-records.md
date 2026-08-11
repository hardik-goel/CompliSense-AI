# ADR 0007 — Records are generated deterministically; only prose is AI-drafted

## Status

Accepted (2026-08-11). Implemented in `compliance/ropa.py`, `compliance/dfd.py`,
`saas/app/ropa_api.py`; contrasted with `compliance/copilot.py`,
`saas/app/artefacts_api.py`.

## Context

Clients need artefacts they do not have: a privacy notice, a retention schedule, a Record of
Processing Activities, a data-flow diagram. An LLM can draft all of them, and drafting all of
them with an LLM is the obvious build.

It is also wrong for half of them, because the artefacts are not the same kind of object:

- A **privacy notice** is *prose*. It is an argument, written in a house style, that a lawyer
  will edit. An LLM draft is a good first draft, and a wrong sentence is visible to the
  reviewer reading it.
- A **ROPA** is a *record*. Every cell asserts a fact about the client's systems: this store
  holds these categories, kept this long, in this region, shared with this processor. An LLM
  asked to produce one will produce a *plausible* one. Plausible-and-wrong is undetectable by
  reading — it looks exactly like correct — and it is precisely the artefact a regulator or
  acquirer will test against reality.

A fabricated register is worse than a missing register. A missing one is a known gap. A
fabricated one is a false assurance that survives until someone checks.

## Decision

Split artefacts by kind and generate each accordingly.

**Deterministic (no LLM, no approval step needed):**
`compliance/ropa.py` and `compliance/dfd.py` are pure functions over confirmed inputs, in
strict priority: declared processing activities → names-only data-flow inference → Tier-0
manifest answers. Unsourced fields are stamped `UNKNOWN` per [[0004-unknown-is-a-gap]]. There
is no approval gate because there is nothing to approve — the output is a projection of facts
the client already gave us. The DFD is derived from the ROPA rather than built in parallel, so
the picture cannot disagree with the table ([[0011-diagram-derives-from-register]]).

**AI-drafted (grounded, consent-gated, approval-gated):**
Prose artefacts go through the copilot: grounded in the cited rule plus confirmed non-PII
facts, requiring explicit `consent_to_send`, stamped "DRAFT — REQUIRES LEGAL REVIEW", and
exported only after the client explicitly approves each one.

The export bundle carries both, labelled distinctly, and the README tells the client which is
which.

## Consequences

- **Positive.** The ROPA is reproducible and auditable: same facts in, same register out. It
  can be diffed across time and defended line by line.
- **Positive.** Cheap and fast — no token cost, no latency, works offline, testable with
  ordinary unit tests rather than LLM evals.
- **Positive.** The honest completeness figure becomes a feature: "95%, and here is the one
  field only you can supply" is a better sales artefact than a fabricated 100%.
- **Negative.** The register is only as rich as the client's declarations. Without declared
  processing activities, purposes are `UNKNOWN` and the document looks thin. This is accurate
  and still disappointing on first run.
- **Negative.** Two generation paths to maintain, with a judgement call at the boundary for
  each new artefact type. The test is: *does a wrong cell look identical to a right one?* If
  yes, it must be deterministic.

## Alternatives considered

- **LLM-draft the ROPA from the manifest.** Rejected: it is exactly the fabrication risk, and
  the failure is silent.
- **LLM-draft then validate deterministically.** Rejected as needless: if the deterministic
  rules can validate the output, they can produce it.
- **Refuse to generate a ROPA until fully declared.** Rejected: a partial register with
  honest `UNKNOWN`s is genuinely useful and shows the client exactly what to do next.

## Related

[[0004-unknown-is-a-gap]] · [[0011-diagram-derives-from-register]] ·
[[0009-artefact-provenance-and-staleness]]
