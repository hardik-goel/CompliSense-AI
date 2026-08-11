# ADR 0008 — The watcher detects; a human decides. It never edits a rule

## Status

Accepted (2026-07-18). Implemented in `compliance/regwatch.py`, `saas/app/regwatch_api.py`,
`saas/app/regwatch_cron.py`.

## Context

Rulepacks encode law, and law moves: enforcement dates shift, Rules are notified, the EU AI
Act gains guidance. A rulepack nobody maintains becomes wrong without anyone noticing, and a
compliance product built on a silently-wrong rulepack is worse than no product.

The tempting automation is end-to-end: watch the sources, have an LLM read the diff, patch the
rulepack, re-score everyone. Every client is always current, with no human in the loop.

That system has a failure mode with no floor. An LLM misreads a consultation paper as an
enacted amendment; a rule's enforcement date silently moves; every client is re-scored against
a law that does not exist; the reports they filed on our output are wrong. Nobody finds out
until a regulator asks. There is no bound on the damage and no audit trail explaining how the
rule came to say what it says.

## Decision

**Detection is automated. Interpretation is drafted. Application is human, always.**

The pipeline, with the gate stated at each step:

1. **Watch** — the union of every `source_url` cited by a rule ([[0002-rulepack-schema-v2]])
   and a seed watchlist in `regwatch_sources.yaml` that covers sources no rule cites yet, so
   we notice a new instrument *before* a rule exists for it.
2. **Normalise and hash** — `normalize_text()` collapses whitespace so cosmetic reflow does
   not read as legal change. Same instinct as fingerprinting only legally material fields in
   [[0009-artefact-provenance-and-staleness]]: a signal that cries wolf is not a signal.
3. **Detect** — first sighting is a baseline, not an alert.
4. **Route** — map the diff to affected rules by source URL *and* by citation reference, so a
   diff mentioning "Article 50" reaches the rules citing Article 50 even from an index page.
5. **Triage** — `propose_action()` returns `date_change` / `new_rule_stub` / `review_only`.
   A hint for the reviewer, never an instruction.
6. **Draft** — an LLM may write a plain-language summary and a YAML **patch scaffold** under
   `rulepacks/proposals/`. It is stamped `DRAFT PROPOSAL — applied to NOTHING`.
7. **Human gate** — an admin approves or rejects. Approval **stages** a patch that still needs
   a human merge. `auto_applied` is `False` everywhere in the codebase and there is no path
   that sets it True.

Separately, `saas/app/freshness_api.py` joins pending proposals to the artefacts a client is
holding, so the client gets an early warning ("a source moved; these two documents may be
affected") explicitly labelled as *not yet a rule change*.

## Consequences

- **Positive.** Rulepack history is a reviewable audit trail: every rule change traces to a
  detected source change, a named reviewer, and a merged patch.
- **Positive.** No unbounded automated failure. The worst case is a missed change — bad, but
  recoverable and visible — rather than a confidently wrong law applied to every client.
- **Positive.** Consistent with [[0001-readiness-not-compliance]]: the system never asserts a
  legal position no human has taken.
- **Negative.** Latency between a real change and an updated rulepack, bounded by reviewer
  availability. This is an operational commitment, not just a design choice.
- **Negative.** Hash-based detection is noisy on pages with dynamic chrome; the reviewer eats
  the false positives.
- **Negative.** Requires a qualified human in the loop permanently — a real cost that scales
  with jurisdictions covered.

## Alternatives considered

- **Fully automated rulepack updates.** Rejected: unbounded downside, no audit trail, and it
  makes us the author of a legal position nobody reviewed.
- **Manual review with no watcher.** Rejected: the failure is silent and total. Detection is
  the cheap half.
- **Subscribe to a commercial regulatory-change feed.** Not rejected on principle — a good
  future input to step 1. It does not remove the need for the gate at step 7.

## Related

[[0002-rulepack-schema-v2]] · [[0009-artefact-provenance-and-staleness]] ·
[[0013-superseded-packs-stay-registered]]
