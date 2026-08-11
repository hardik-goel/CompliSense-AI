# Architecture Decision Records

The decisions that shape CompliSense-AI, and — more usefully — the reasoning and the costs
behind each one. Read this before proposing a change to the engine, the rulepacks, or how
artefacts are produced. If a change contradicts one of these, that is fine, but it needs a new
ADR that supersedes the old one rather than a quiet edit.

These are kept honest by `tests/test_adr.py`, which enforces structure, numbering, and that
the index below matches the files on disk.

## The through-line

Almost every decision here is the same instinct applied to a different surface:

> **Never assert more than the evidence supports, and make every omission a decision on the
> record rather than a silence.**

That is why unknowns are gaps rather than passes, why non-applicable rules are printed as
`NOT_APPLICABLE` rather than filtered out, why the watcher never edits a rule, why a register
is generated deterministically rather than written by an LLM, and why an unstamped artefact is
reported as unverifiable rather than fine.

## Index

| # | Decision | One-line rationale |
|---|---|---|
| 1 | [Report readiness, never a compliance determination](0001-readiness-not-compliance.md) | We assess declared facts, not the world — and most DPDP duties aren't in force yet. |
| 2 | [Rulepack schema v2](0002-rulepack-schema-v2.md) | A finding you can't trace to a source can't be defended, reviewed, or watched. |
| 3 | [Applicability gating](0003-applicability-gating.md) | Scoring a startup on SDF duties is noise; silently skipping them is worse. |
| 4 | [Unknown is a gap](0004-unknown-is-a-gap.md) | Rounding in the client's favour manufactures false comfort. |
| 5 | [Names-only PII inference](0005-names-only-pii-inference.md) | Reading values would make a privacy product a Data Fiduciary over its customers' data. |
| 6 | [Local agent trust model](0006-local-agent-trust-model.md) | Compute goes to the data; the data does not come to us. |
| 7 | [Deterministic records, AI-drafted prose](0007-deterministic-records.md) | A fabricated register looks exactly like a correct one. Prose doesn't. |
| 8 | [Human-gated regulatory watcher](0008-human-gated-regwatch.md) | Automated law-reading has a failure mode with no floor. |
| 9 | [Artefact provenance and staleness](0009-artefact-provenance-and-staleness.md) | A stale document is a false assurance with a plausible date on it. |
| 10 | [The eight-domain lens](0010-eight-domain-lens.md) | Present DPDPA the way the market already reads it — as a proven view, not a second truth. |
| 11 | [Diagram derives from the register](0011-diagram-derives-from-register.md) | Two generators would drift; a projection cannot. |
| 12 | [Consent-gated persistence, non-PII analytics](0012-consent-gated-persistence.md) | We must be able to answer our own questionnaire honestly. |
| 13 | [Superseded packs stay registered](0013-superseded-packs-stay-registered.md) | A past assessment must remain reproducible against the pack that produced it. |
| 14 | [The pack follows the cited rules](0014-pack-follows-the-cited-rules.md) | Jurisdiction is a property of the rules an artefact rests on, not of its project. |

## Format

Each ADR carries **Status · Context · Decision · Consequences · Alternatives considered**.
Consequences list the costs as well as the benefits — an ADR with only upside in it has not
been thought through, and will not survive contact with someone doing diligence.

## Still open

Decisions deliberately *not* taken yet, recorded so their absence is also on the record:

- **Billing and plan enforcement.** `saas/app/plans.py` defines tiers; no payment integration
  exists. Needs an ADR when one is chosen.
- **Consent capture, data-principal-rights and breach-notification runtimes.** Currently the
  product assesses whether these processes exist; it does not run them. Building any of them
  is a category change and needs its own ADR.
- **An EU AI Act domain lens.** [[0010-eight-domain-lens]] is DPDP-specific by design.
- **Client-side value sampling.** The revisitable half of
  [[0005-names-only-pii-inference]] — only ever as a new ADR, never as a quiet change.
