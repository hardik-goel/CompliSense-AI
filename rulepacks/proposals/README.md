# Rulepack change proposals

Approved regulatory-change proposals land here as **YAML patch stubs** (one file per
proposal, named `<change_id>.yaml`), written by the regwatch review endpoint
(`POST /api/v1/regwatch/proposals/{change_id}/review` with `decision: approved`).

**These are scaffolds, not applied changes.** The engine NEVER edits a live rulepack.
Each stub records the detected source change, the affected rule IDs (matched by URL and
by citation), the proposed action (`date_change` / `new_rule_stub` / `review_only`), and a
`suggested_edit` block a human fills in and applies by hand — then regenerates
`LEGAL_REVIEW_NEEDED.md` via `scripts/gen_legal_review.py`.

Rejected proposals are archived (status `rejected`) and no file is written.
