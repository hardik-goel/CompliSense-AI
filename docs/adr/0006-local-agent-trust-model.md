# ADR 0006 — Scanning runs on the client's machine, under the client's credentials

## Status

Accepted. Implemented in `agent/` (packaged binary), `agent/collectors/`, `connectors/`.

## Context

To assess artefacts we must read them: privacy notices in Confluence, model cards in MLflow,
DPAs in Google Drive, risk registers in a repo. The default SaaS shape is "connect your
sources, we index them". That shape requires the client to hand us:

- credentials with read access to their document estate, and
- a copy of documents that routinely contain personal data, commercial terms and security
  detail.

For the Indian mid-market and BFSI buyers this is the deal-breaker, not a detail. It also
contradicts [[0005-names-only-pii-inference]]: promising we never read values while holding a
mirror of the client's Confluence is not a promise anyone should believe.

## Decision

**Compute goes to the data; the data does not come to us.**

- The scanner ships as a downloadable agent that runs on the client's machine or in their VPC.
- It reads documents with the **client's own local credentials**. Those credentials are never
  transmitted to us and never stored by us.
- Document **contents never leave the client's machine**. What is uploaded is the scan result:
  rule outcomes, category names, matched field names, scores.
- Only **non-secret configuration** (which sources were declared, of what type) is stored
  server-side.
- The hosted Tier-1 connectors (AWS / GCP / Azure / GitHub) are read-only, least-privilege and
  metadata-only — a deliberately narrow exception that never touches document bodies.
- Because scanning is client-side, we cannot force a re-scan. Monitoring raises **overdue
  alerts**, not forced scans ([[0008-human-gated-regwatch]] shares this instinct: detect and
  prompt, never act unilaterally).

## Consequences

- **Positive.** A genuine, checkable security story, and the main reason a regulated buyer
  will take a meeting with a company this size.
- **Positive.** Data-residency questions largely evaporate — the data never moves.
- **Positive.** Smaller breach surface, smaller compliance burden on ourselves.
- **Negative — the largest operational cost in this ADR set.** We must build, sign, package
  and support a cross-platform binary (`CompliSenseAgent.spec`, PyInstaller). Distribution,
  updates and "it won't launch on my Mac" are permanent support load.
- **Negative.** Onboarding friction: a download beats a checkbox on trust and loses on speed.
- **Negative.** No server-side continuous monitoring of documents. We see a point-in-time
  result when the client chooses to run a scan.
- **Negative.** Debugging is harder — we cannot reproduce a client's scan without their data,
  by construction.

## Alternatives considered

- **Hosted ingestion with encryption at rest.** Rejected: encryption does not change who holds
  the data, which is the actual objection.
- **Ephemeral processing (ingest, score, delete).** Rejected: "we delete it afterwards" is
  unverifiable by the client, and the window is exactly when a breach would matter.
- **Browser-based local scanning (WASM).** Attractive — no install — but cannot reach a local
  filesystem, S3 with local creds, or a corporate Drive. Revisit if the artefact-upload path
  ever becomes the dominant flow.

## Related

[[0005-names-only-pii-inference]] · [[0012-consent-gated-persistence]]
