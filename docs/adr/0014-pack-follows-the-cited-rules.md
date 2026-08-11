# ADR 0014 — An artefact's rulepack is chosen by the rules it cites

## Status

Accepted (2026-08-11). Implemented as `pack_for_rules()` in `saas/app/freshness_api.py`;
consumed by `saas/app/ropa_api.py` and `saas/app/artefacts_api.py`.

## Context

Provenance stamps ([[0009-artefact-provenance-and-staleness]]) need a rulepack to fingerprint
against. The first implementation hardcoded one — `PROVENANCE_PACK = "dpdp_india_extended_v2"`
— because the ROPA happened to cite DPDP rules.

Three things were wrong with that, in increasing order of seriousness:

1. An **EU AI Act** artefact (technical documentation, risk-management system) stamped against
   the DPDP pack produces a stamp whose every dependency lands in `missing_rule_ids`. It looks
   like a stamp and carries no information.
2. Deriving the pack from the **project** instead is no better. A project can be in scope for
   both DPDP and the EU AI Act; its documents are not all in scope for both. The privacy
   notice is DPDP; the Art. 11 technical documentation is EU. One project, two jurisdictions,
   per artefact.
3. A hardcoded constant silently becomes wrong the moment a pack is superseded
   ([[0013-superseded-packs-stay-registered]]), and nothing fails — the stamp just quietly
   references a stale pack id.

## Decision

**Jurisdiction is a property of the rules an artefact rests on, not of the project it belongs
to and not of a constant.**

- `pack_for_rules(rule_ids)` scans the current packs and returns the one covering the most of
  the cited rules.
- Callers pass what the artefact actually cites: the ROPA passes its `supports_rules`; an
  AI-drafted artefact passes the single `rule_id` its catalog entry closes.
- When **nothing** covers the rules, it returns `None` and the caller records an *unstamped*
  artefact rather than stamping against an arbitrary pack. Consistent with
  [[0004-unknown-is-a-gap]]: an honest blank beats a confident wrong answer.
- `CURRENT_PACKS` is the ordered preference list, so a superseded pack is never selected while
  a current one covers the same rules.

## Consequences

- **Positive.** EU artefacts get EU stamps and DPDP artefacts get DPDP stamps, with no
  per-caller configuration and no project-level jurisdiction field to keep in sync.
- **Positive.** Adding a jurisdiction means adding a pack to `CURRENT_PACKS` — the stamping
  path needs no change.
- **Positive.** Removes a constant that would have rotted silently.
- **Negative.** Pack loading happens on the stamping path. Mitigated by loading lazily and
  caching per request; it is still more I/O than reading a constant.
- **Negative.** "Most rules covered" is a heuristic. An artefact citing rules that genuinely
  straddle two packs gets stamped against one of them, and the rest land in
  `missing_rule_ids`. Acceptable today because no artefact does that; it would need a
  multi-pack stamp if one ever did.
- **Negative.** The preference order in `CURRENT_PACKS` is a maintenance obligation — a new
  pack version must be added at the front or artefacts keep stamping against the old one.

## Alternatives considered

- **Hardcode per artefact type.** Rejected: the same rot as one global constant, multiplied by
  the number of artefact types.
- **Store a jurisdiction on the project.** Rejected: wrong granularity. Jurisdiction varies per
  document within a project.
- **Store the pack id on each catalog entry.** Closer, but it duplicates a fact already
  derivable from the rule id, and duplicated facts drift.

## Related

[[0009-artefact-provenance-and-staleness]] · [[0013-superseded-packs-stay-registered]] ·
[[0004-unknown-is-a-gap]]
