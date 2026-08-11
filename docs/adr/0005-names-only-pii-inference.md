# ADR 0005 — Infer personal data from field NAMES only, never from values

## Status

Accepted (2026-06-27). Non-negotiable. Implemented in `compliance/pii.py`,
`compliance/dataflow.py`, `saas/app/pii_api.py`.

## Context

To score a client we need to know which categories of personal data they hold and where. We
could learn that by sampling their data — read a column, see `9876543210`, conclude "phone".
Accuracy would be far better than name matching.

It would also make a privacy-compliance product into a personal-data processor. We would be
a Data Fiduciary over our customers' Data Principals, inheriting notice, consent, security,
breach, retention and cross-border duties over data we have no business holding. The reputational
exposure is worse than the legal one: one incident and the company is over.

There is no version of this trade that is worth taking.

## Decision

Inference runs on **names only** — column names, JSON keys, form field names. Never values.

- `PII_PATTERNS` maps keyword → category with a confidence. Short keywords (≤3 chars) match
  only as whole tokens, so `pan` does not fire on `company`.
- The only evidence surfaced is the **matched field name** (`evidence_field_names`).
- Connectors are read-only and metadata-only; credentials are never stored.
- Output is a **suggestion**, not a write. Nothing reaches the manifest until the client
  accepts it through `/pii/inferences/{id}/apply`.
- Persistence of an inference is consent-gated; without consent it is ephemeral.
- The same stance carries into the ROPA: inferred rows show categories and matched field
  names, never data.

## Consequences

- **Positive.** "Your data never leaves your machine, and we never read a value" is true
  without qualification. It is the strongest differentiator we have against platforms that
  require an upload, and it is the objection-killer for BFSI and health buyers.
- **Positive.** Radically smaller breach blast radius. We hold declarations and hashes.
- **Positive.** Keeps us out of Data-Fiduciary status over customer data.
- **Negative.** Lower recall. A column called `col_7` holding Aadhaar numbers is invisible to
  us. We accept the miss; [[0004-unknown-is-a-gap]] means it surfaces as unknown, not as pass.
- **Negative.** False positives on names (`name` fires at low confidence on `filename`).
  Mitigated by confidence levels and human confirmation, not by reading values.
- **Negative.** We cannot offer data discovery/classification the way OneTrust-class products
  do. That is a permanent product boundary, and it is the right one.

## Alternatives considered

- **Sample values client-side in the agent, send only categories.** Genuinely tempting: the
  values never leave the machine. Rejected *for now* because the claim degrades from "we never
  read values" to "we read values but promise not to keep them" — the second sentence is the
  one an enterprise security reviewer stops at. Revisitable as its own ADR, never as a quiet
  change.
- **Regex-match values for known formats (Aadhaar, PAN).** Rejected: same objection, and it
  requires reading exactly the most sensitive identifiers.
- **Ask the client to self-declare only.** That is the Tier-0 baseline; name inference
  corroborates it. Declaration alone was too weak to catch what clients forget they hold.

## Related

[[0006-local-agent-trust-model]] · [[0004-unknown-is-a-gap]] · [[0012-consent-gated-persistence]]
