# DATA_HANDLING.md — how CompliSense handles data

> Status: 2026-06-26. Dogfooding the DPDP notice standard: this document itemises what
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

### 4. LLM-assisted features (Phase 7 — PLANNED)
- No user artefacts/personal data may be sent to a third-party model without **explicit,
  specific, opt-in consent that names the provider**. A local/no-egress model path must be
  offered for sensitive scans. The data flow must be shown to the user before any egress.

## Open items
- [ ] Document the Phase-1 web tool data flow here once built.
- [ ] Confirm and document an account-deletion / data-export path for stored findings.
- [ ] Ensure user-facing copy says "we do not store your source artefacts / personal
      data" rather than an absolute "we store nothing," since findings/metadata are stored.
