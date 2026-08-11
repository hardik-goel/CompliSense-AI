# ADR 0001 — Report readiness, never a compliance determination

## Status

Accepted (2026-06-26). Load-bearing for every other ADR in this set.

## Context

CompliSense assesses organisations against the DPDP Act 2023 / DPDP Rules 2025 and the EU AI
Act. The obvious product is a verdict: **COMPLIANT / NON-COMPLIANT**. That verdict is the one
thing we are least entitled to issue.

Three reasons, in increasing order of seriousness:

1. **We assess declared facts, not the world.** Every input is either an answer the client
   typed, a document they gave us, or metadata a read-only connector saw. A client who says
   "yes, we have security safeguards" produces the same score whether or not the safeguards
   exist. That is a statement about their declaration, not about their compliance.
2. **Most DPDP operational obligations are not yet in force.** The Rules were notified in
   November 2025 with substantive compliance due 13 May 2027. Telling a client in 2026 that
   they are "non-compliant" with a duty that does not yet bind them is simply false.
3. **Compliance determinations are a regulated activity in substance.** A tool that issues
   them is holding itself out as giving legal advice. Our rulepacks are, as of this writing,
   *pending professional legal review* (`LEGAL_REVIEW_NEEDED.md`, 44 open items).

## Decision

The engine reports **readiness**, framed as *prepare-by*, and never a compliance verdict.

- Rules carry `status`, `enforcement_date` and `date_status`; findings are rendered through
  `readiness_framing()` so a not-yet-in-force duty reads as "prepare by <date>", not a breach.
- Every client-facing surface — public tool, project readiness, PDF, evidence pack, generated
  artefacts, emails — carries the not-legal-advice framing.
- Every generated document is stamped **"DRAFT — REQUIRES LEGAL REVIEW"**.
- The word "compliant" does not appear as a verdict anywhere in the product.

## Consequences

- **Positive.** The product is honest, defensible in diligence, and shippable before legal
  sign-off completes. It also does not compete on a claim we would lose on.
- **Positive.** It survives regulatory change: "readiness against the rules as they stand on
  date X" degrades gracefully, where "compliant" would become a lie the moment the law moved.
- **Negative.** It is a harder sell. Buyers ask for a green tick, and "readiness score" needs
  a sentence of explanation that "compliant" does not.
- **Negative.** It constrains marketing copy permanently, including in places (landing page,
  emails) where a stray "get compliant" is an easy mistake to make.
- **Constraint on all future work.** Any feature that would imply a determination — a
  certificate, a badge, a pass/fail seal — is out of scope until counsel signs off and the
  framing is revisited deliberately, as its own ADR.

## Alternatives considered

- **Issue compliance verdicts.** Rejected: unsupportable on the evidence we actually hold,
  and it converts a software liability into a professional-advice liability.
- **Verdicts gated behind a lawyer-review flag.** Rejected as of now: it puts the dangerous
  behaviour in the codebase awaiting one config flip, and the framing leaks into UI copy long
  before the flag is ever set.
- **Say nothing and let the score imply the verdict.** Rejected: implication without a stated
  frame is the worst of both — the client hears "compliant" and we disclaim having said it.

## Related

[[0004-unknown-is-a-gap]] · [[0002-rulepack-schema-v2]] · [[0007-deterministic-records]]
