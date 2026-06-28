# DATA_HANDLING.md — how CompliSense handles data

> Status: 2026-06-28 (updated through Phase 8). Dogfooding the DPDP notice standard: this document itemises what
> data each component touches, why, where it goes, and how long it is kept. Brand promise:
> **"without storing your data."** Where any tension exists, it is flagged here explicitly
> rather than hidden.

## TL;DR
- **Local agent (scanner):** runs on the user's machine. It reads the user's project
  artefacts locally to evaluate rules. **Raw artefact file content does not leave the
  machine.** Only structured *findings* (rule id, status, evidence summary such as missing
  field names and a truncated file hash) are produced.
- **Upload to SaaS (optional):** when the user uploads a scan, the backend stores the
  **findings JSON + a results summary**, not the raw documents. This is the deliberate
  free/paid + privacy boundary.
- **Public "DPDP Readiness Score" web tool (Phase 1, not yet built):** anonymous answers
  must be **ephemeral or explicitly consented**; signed-in assessments persisted to the
  user's account. To be documented in full when built.

## Component-by-component

### 1. Local agent / CLI (`run_scan.py`, `agent/scanner.py`)
- **Reads:** files under the `--project-path` the user points at (privacy notices, model
  cards, config, etc.), and the bundled rulepacks.
- **Produces:** `compliance_findings.json` on the user's disk: per-rule status, severity,
  citations, evidence summary (e.g. `missing_fields` names, truncated `file_hash`),
  remediation text. **No raw file bodies are embedded.**
- **Network:** none required to scan. Egress happens only if the user explicitly uploads
  (below) or enables an LLM feature (see §4).
- **Retention:** entirely on the user's machine; user controls deletion.

### 2. Upload API (`POST /api/v1/upload-scan`, `saas/app/`)
- **Receives:** the findings JSON + results summary produced above.
- **Stores (MongoDB Atlas):** findings/metadata and the results summary, associated with
  the authenticated account. **It does NOT store the user's raw artefacts/source files.**
  ⚠️ *Tension to be transparent about:* findings can themselves contain small evidence
  snippets (field names, hashes). These are metadata about compliance posture, not the
  underlying personal data — but the "without storing your data" claim means "we do not
  store your source artefacts / personal data," which should be stated precisely in
  user-facing copy.
- **Auth:** JWT per user; an admin token guards privileged endpoints (see SECURITY.md).
- **Retention:** for signed-in users, retained as scan history (Phase 2). Provide deletion
  on account request.

### 3. Public web Readiness tool (Phase 1 — IMPLEMENTED)
Endpoints: `GET/POST /api/v1/readiness/*` (`saas/app/readiness.py`); UI:
`landing-page/app/readiness/`.
- **Anonymous visitors:** questionnaire answers are processed in-request to compute the
  score + top-3 teaser and are **NOT persisted** (ephemeral). The `score` endpoint writes
  nothing to the database for anonymous users. The UI states this on the form.
- **Signed-in users:** the full report is returned, and the assessment is persisted to the
  user's account **only if they pass `consent_to_store: true`** (collection
  `readiness_assessments`: user_id, timestamp, answers, score, summary). Without consent,
  nothing is stored. Retrievable/deletable per account.
- **Analytics:** first-party only (`saas/app/analytics.py`, collection `analytics_events`).
  Records non-PII funnel events (`readiness_completed`, `signup`) with safe properties
  (score bucket, authenticated flag, pack id) — a blocklist strips email/answers/name/ip.
  No third-party tracker; consistent with the privacy promise.

### 4. Tier-1 connector discovery (Phase 3 — IMPLEMENTED)
Endpoints: `POST /projects/{id}/connectors/{provider}/discover` (`saas/app/connectors_api.py`);
engine: `connectors/`.
- **Credentials are NEVER stored.** They arrive in the request body, are filtered to the
  exact accepted read-only kwargs (blocking `client_factory`/`http_get` injection), used for
  the single read-only discovery call, then dropped (`connectors_api.py`: `creds = None`).
- **Reads (read-only, least-privilege):** cloud/SCM *resource metadata* — bucket/account
  names, encryption/public-access flags, region, MFA/logging status. No object contents, no
  personal data.
- **Stores (MongoDB `connector_discoveries`):** normalized **signals + manifest suggestions
  only**, and **only with `consent_to_store: true`**. Never credentials, raw API payloads, or
  resource ARNs. The exact data path is echoed to the user (`data_sent`/disclaimer).
- **Retention:** per account; deletable on request.

### 5. Tier-2 PII / data-flow inference (Phase 4 — IMPLEMENTED)
Endpoints: `POST /projects/{id}/pii/infer` (`saas/app/pii_api.py`); engine: `compliance/pii.py`,
`compliance/dataflow.py`.
- **Reads:** the **NAMES** of data fields/columns/JSON keys the user supplies (e.g.
  `user_email`, `pan_number`). **Never field values / personal data.**
- **Stores (MongoDB `pii_inferences`):** the submitted field **names** + inferred categories +
  suggestions, **only with `consent_to_store: true`**. Field names are metadata, not personal
  data values; documented here for precision.
- **Retention:** per account; deletable on request.

### 6. LLM remediation copilot (Phase 7 — IMPLEMENTED; live third-party egress)
Endpoints: `POST /projects/{id}/copilot/remediate` (`saas/app/copilot_api.py`); engine:
`compliance/copilot.py`.
- **Provider:** Anthropic (`claude-opus-4-8`) via the Anthropic API. **This is real egress to a
  third party.**
- **Consent:** the call runs **only** with explicit `consent_to_send: true`.
- **What is sent:** the cited rule text + the project's confirmed, **non-PII** manifest facts
  (`discovered_manifest` booleans/categories). **Never** raw artefacts, field values, or
  personal-data values. The exact fact keys + citation sent are echoed back in `data_sent`.
- **What is stored:** the copilot response is returned to the user; it is not persisted by
  default. Generated documents are stamped "DRAFT — REQUIRES LEGAL REVIEW".
- **No fully-local/offline model path yet** — egress is consent-gated and minimised, but a
  no-egress option is not implemented (tracked below).

### 7. Evidence export (Phase 8 — IMPLEMENTED)
- `GET /projects/{id}/evidence[/export.html]` assembles a pack from **summaries only** —
  readiness + citations, posture history, alert/discovery/PII *summaries*, the confirmed
  manifest. No credentials, raw artefacts, or personal-data values are included.

## Public-tool privacy notice (DPDP-grade) — OPEN
- `landing-page/app/privacy/page.tsx` is a generic **website** privacy policy; it does not yet
  cover the readiness tool as a DPDP data-fiduciary notice (data-principal rights, purpose,
  retention, grievance officer, consent withdrawal, cross-border). A DPDP-grade notice for the
  tool is drafted as a counsel checklist in `docs/TERMS_NOTES.md` and must be reviewed by
  counsel before publishing.

## Open items
- [x] Document the Phase-1 web tool data flow (see §3).
- [x] Document connector (§4), PII (§5), copilot/LLM egress (§6), evidence (§7) flows.
- [ ] Offer a local/no-egress model path for the copilot, or keep it strictly consent-gated.
- [ ] Publish a DPDP-grade privacy notice for the public readiness tool (counsel review).
- [ ] Confirm and document an account-deletion / data-export path for stored findings,
      discoveries, PII inferences, and assessments.
