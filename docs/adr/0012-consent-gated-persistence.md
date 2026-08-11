# ADR 0012 — Consent-gated persistence and first-party, non-PII analytics

## Status

Accepted (2026-06-27). Implemented in `saas/app/readiness.py`, `saas/app/pii_api.py`,
`saas/app/analytics.py`, `saas/app/leads_api.py`.

## Context

A privacy-compliance product that is careless with its own users' data is not merely ironic —
it is unsellable. The buyer's security reviewer will assess *us* against the same standard we
are selling them, and the public readiness tool is the first thing they will look at.

The default startup build works against us here: drop in a third-party analytics tag, store
every questionnaire submission for the funnel, retain everything by default because storage is
cheap and the data might be useful later. Each of those is a finding when applied to us.

The public readiness questionnaire is the sharpest case. Its answers are a detailed profile of
an identifiable company's compliance weaknesses — the sort of thing that is genuinely damaging
if breached, and genuinely valuable to us commercially. The commercial pull and the right
answer point in opposite directions.

## Decision

**Persistence requires consent. Analytics never touches personal data.**

- **Anonymous** use of the public tool is **ephemeral**: the score and a top-three teaser are
  computed and returned; nothing is stored.
- **Signed-in** use returns the full report, and it is persisted to `readiness_assessments`
  **only** when the request carries `consent_to_store: true`. Absent consent, the report is
  returned and dropped.
- The same gate applies to PII/data-flow inferences (`consent_to_store`) and to sending facts
  to an LLM (`consent_to_send` — a separate consent, because it is a separate disclosure to a
  separate party).
- **Analytics is first-party and non-PII.** `saas/app/analytics.py` records funnel events
  (`readiness_completed`, `signup`) into our own `analytics_events`, through a **blocklist**
  that strips email, name, IP and questionnaire answers. Scores are recorded as buckets, not
  values. There is **no third-party tracker anywhere in the product.**
- Lead capture is explicit and separate: an email is collected only when the user submits the
  lead form, with DPDP consent language shown at the point of collection.

## Consequences

- **Positive.** We can answer our own questionnaire honestly. That is the single most useful
  thing in an enterprise security review.
- **Positive.** Small breach surface: no third-party trackers, no ambient store of company
  compliance profiles.
- **Positive.** Consistent with [[0005-names-only-pii-inference]] and
  [[0006-local-agent-trust-model]] — the same stance applied to our own funnel.
- **Negative — a real commercial cost.** We cannot see who abandoned the questionnaire, or
  re-market to anonymous users, or analyse historical answers we chose not to keep. Standard
  growth tooling is unavailable by construction.
- **Negative.** Bucketed analytics limits product insight. We know the shape of the funnel,
  not the individuals in it.
- **Negative.** More engineering: consent flags must be threaded through every write path, and
  the blocklist needs maintenance as event payloads evolve.

## Alternatives considered

- **Store everything, disclose it in the privacy policy.** Rejected: lawful is not the bar
  here. We would be holding a database of identified companies' compliance weaknesses.
- **Third-party analytics with IP anonymisation.** Rejected: still a transfer to a processor,
  still a cross-border question, still a finding in our own assessment.
- **Consent defaulted to on with an opt-out.** Rejected: pre-ticked consent is precisely what
  the DPDP consent rules exist to stop, and `consent_mechanism: pre_ticked_or_implied` is a
  *gap* in our own scoring engine. We would be failing our own rule.

## Related

[[0005-names-only-pii-inference]] · [[0006-local-agent-trust-model]] ·
[[0001-readiness-not-compliance]]
