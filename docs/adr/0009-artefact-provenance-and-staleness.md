# ADR 0009 — Stamp every generated artefact with what it was built from

## Status

Accepted (2026-08-11). Implemented in `compliance/provenance.py`,
`saas/app/freshness_api.py`.

## Context

Generating a compliance artefact is the easy half. The hard half is that the law moves and the
document does not. A ROPA generated in August against a rule whose enforcement date shifts in
November is, from November, quietly wrong — and it looks exactly as authoritative as it did
in August. The client keeps it in a folder, hands it to an auditor, and cites it.

That is worse than never generating it. A missing document is a known gap. A stale document
is a false assurance with a plausible date on it.

[[0008-human-gated-regwatch]] tells us when a *source* moved. It does not tell us which
*documents in clients' hands* that invalidates. Without that join, "we monitor the law" is a
claim about our backlog, not a benefit the client receives.

## Decision

Every generated artefact is stamped with a **provenance record**, and staleness is computed
from it rather than guessed.

**The stamp** (`build_provenance`):
- `pack_id` + `pack_version` it was built against;
- for each depended-on rule, a **fingerprint over the legally material fields only**
  (`LEGALLY_MATERIAL_FIELDS`: citations, source URL, status, enforcement date, applicability,
  requirement) — plus per-field hashes so a later comparison can name *which* field moved;
- the DPDPA domains the artefact claims to cover, **and the rules each of those domains held
  at stamping time**.

Hashes, never values: the stamp travels with the artefact and must not become a partial copy
of the rulepack in the database.

**The assessment** (`assess_freshness`) returns three states, not two:

| Status | Meaning |
|---|---|
| `fresh` | Nothing this artefact depends on has moved. |
| `review` | The pack moved, but not in a way that touches this artefact. |
| `stale` | A depended-on rule changed or vanished, or a new rule landed in a covered domain. |

The middle state is the important one. Collapsing `review` into `stale` would flag artefacts
on every unrelated pack bump, and a flag that fires constantly is a flag people turn off.
The same reasoning drives fingerprinting only material fields: a reworded internal title is
not a change in the law and must not raise an alarm.

**The join** (`impacted_artefacts`) maps changed rule IDs to the artefacts they invalidate,
either by direct dependency or because the rule belongs to a domain the artefact covers. An
artefact with no stamp is reported `unstamped` — we cannot prove it is unaffected, and
silently passing it is the lie the stamp exists to prevent ([[0004-unknown-is-a-gap]]).

**The client is told, rather than having to ask.** `evaluate_artefact_freshness()` and
`evaluate_regwatch_exposure()` run in the monitoring cron alongside the scan-overdue sweep,
raising `artefact_stale` and `regwatch_exposure` alerts (deduped per day). Only `stale`
alerts — a `review` result is deliberately silent, because an alert that fires on every
unrelated pack bump is one the client learns to ignore, and then the real one is missed too.

**Nothing regenerates automatically.** Same gate as [[0008-human-gated-regwatch]]: a system
that silently rewrites the client's compliance evidence is one nobody can audit.

## Consequences

- **Positive.** "Is this still current?" becomes answerable per document, with the reason and
  the changed field named.
- **Positive.** Turns regulatory monitoring from a backlog activity into delivered value.
- **Positive.** Enables an early-warning view on *pending* proposals, before any rule edit.
- **Negative.** Storage and a schema commitment: stamps must be migrated as
  `LEGALLY_MATERIAL_FIELDS` evolves. Adding a field silently invalidates every prior stamp.
- **Negative.** The domain baseline was learned the hard way — without it, every freshly
  generated artefact reported itself stale on day one, because covered domains contain many
  rules the artefact never cited. Regression-tested in `tests/test_provenance.py`.
- **Negative.** Staleness is only as good as the rulepack's currency. It measures drift from
  *our* pack, not from the law itself. Honest framing required in the UI.

## Alternatives considered

- **Timestamp only ("generated 3 months ago").** Rejected: age is not staleness. A two-year-old
  register against an unchanged rule is fine; a one-week-old one against a moved date is not.
- **Store the full rule text and diff it.** Rejected: turns every artefact record into a copy
  of the rulepack, and per-field hashes give the same answer without the copy.
- **Regenerate automatically on rule change.** Rejected: silently rewriting the client's
  evidence destroys the audit trail, and the new version may need re-approval.
- **Binary fresh/stale.** Rejected: alarm fatigue, as above.

## Related

[[0007-deterministic-records]] · [[0008-human-gated-regwatch]] · [[0010-eight-domain-lens]] ·
[[0004-unknown-is-a-gap]] · [[0014-pack-follows-the-cited-rules]]
