# TERMS_NOTES.md — liability-limiting checklist for counsel

> **This is NOT a Terms of Service and NOT enforceable language.** It is a checklist of
> points for a qualified lawyer to turn into real Terms of Service / EULA for the
> CompliSense proprietary product. Drafted by engineering on 2026-06-26 to capture the
> liability posture a compliance-readiness SaaS should have. Do not publish as-is.

## Why
CompliSense outputs compliance-**readiness** assessments. The single biggest liability is a
user (or their customer/investor/regulator) treating tool output as a legal determination
of compliance. Terms must foreclose that reading.

## Checklist for counsel

1. **"Informational tool, not legal advice."** State plainly that the service provides
   compliance-readiness tooling and information, not legal advice, and creates no
   attorney–client relationship.

2. **No guarantee of regulatory outcome.** No warranty that using the service results in,
   or evidences, compliance with the DPDP Act/Rules, the EU AI Act, or any law. Results may
   lag the current legal position (laws change; some obligations not yet enforceable).

3. **Readiness, not determination.** Output uses "ready / gaps identified / needs review"
   language; it is not a legal conclusion of "compliant" or "non-compliant."

4. **Enforcement-status disclaimer.** Many obligations (DPDP operational rules ~May 2027;
   EU high-risk ~Dec 2027, provisional) are not yet enforceable; nothing in output asserts
   a present violation.

5. **Limitation of liability.** Cap liability (e.g. fees paid); exclude
   indirect/consequential/regulatory-penalty damages, to the extent permitted by law.

6. **User responsibility to verify.** User is responsible for verifying results against
   primary sources and consulting a qualified practitioner before relying on them.

7. **"As-is" / no warranties.** Disclaim implied warranties (merchantability, fitness)
   to the extent permitted.

8. **Indemnity considerations.** Consider user indemnity for misuse (e.g. presenting output
   to third parties as a guarantee of compliance).

9. **Data handling commitments.** Align ToS with [`DATA_HANDLING.md`](DATA_HANDLING.md):
   what is stored (findings/metadata, not raw artefacts), retention, deletion, and the
   "without storing your data" claim stated precisely.

10. **Rule-content provenance.** Reference that rule content is pending professional legal
    review (see [`../LEGAL_REVIEW_NEEDED.md`](../LEGAL_REVIEW_NEEDED.md)) and is an
    engineering artefact until a named reviewer signs off.

11. **Third-party / sub-processors.** Disclose hosting (Render/Vercel), database (MongoDB
    Atlas), and any LLM providers; obtain consent for any data egress.

12. **Jurisdiction / governing law.** To be set by counsel.

> Guiding test for any output or term: *"Could a reasonable user mistake this for a
> guarantee of legal compliance?"* If yes, reframe until the answer is no.

---

## DPDP-grade privacy notice for the public readiness tool (counsel checklist)

The public tool collects questionnaire answers and (for signed-in, consented users) stores an
assessment — so CompliSense acts as a Data Fiduciary for that processing. The current
`landing-page/app/privacy/page.tsx` is a generic website policy and is **not sufficient**. A
DPDP-grade notice for the tool must, at minimum (for counsel to draft/finalise):

1. **Identity & contact** of the Data Fiduciary + published **Grievance Officer** contact.
2. **Itemised personal data** collected (questionnaire answers; account email for signed-in).
3. **Purpose** of processing (compute a readiness score; store an assessment on consent).
4. **Legal basis / consent** — explicit, itemised, withdrawable as easily as given.
5. **Retention** — anonymous answers ephemeral (not stored); consented assessments retained
   per account until deletion request.
6. **Data-principal rights** — access, correction, erasure, grievance, nominate.
7. **Sub-processors / cross-border** — hosting (Render/Vercel), DB (MongoDB Atlas), and the
   Anthropic LLM path for the copilot; any transfer outside India.
8. **No third-party trackers** (first-party analytics only; non-PII funnel events).

Until published, the tool relies on the inline "answers not stored for anonymous visitors"
notice + this checklist. Do not represent the generic website policy as the tool's DPDP notice.
