# CompliSense-AI — Build Plan & Audit Checkpoint

> **Purpose:** single source of truth for the end-to-end build across all CLAUDE.md
> prompts (Phases 1–8 + the four grounding/liability/legal-correctness appendices).
> Doubles as a resume checkpoint. Update the status boxes as work lands.
>
> **Created:** 2026-06-26 · **Branch at creation:** Tier-0-Guided-Manifest
> **Discipline:** one feature at a time — propose → confirm → build → report → STOP →
> user tests + branches → next. Nothing deleted without explicit user approval.

---

## ▶ RESUME HERE (checkpoint 2026-06-27, end of day)

**Status:** Phase 0 ✅ + Phase 1 ✅ + **Phase 2 (continuous monitoring) ✅** + Phase 3.1
(Tier-1 connector framework + AWS read-only discovery) ✅.
**Tests:** full suite **124 passed, 0 failed** on `Phase-2` (run: `3.11_venv/bin/python -m
pytest -q`; slow ~4min due to weasyprint — use `-o addopts=""` + target files for speed).
**Branches:** Phase 2 lives on `Phase-2` (PR → `dev` to be raised); `Phase-3` is branched
off Phase-2 and holds 3.1. Phase 2 (2.3/2.4) added on `Phase-2`, then merged forward into
`Phase-3`.

**NEXT: Phase 3 — Tier-1 Connector Discovery.** 3.1 done (`connectors/` pkg). Remaining:
3.2 discovery API endpoints (run discovery via STS assume-role, return + consent-gated
persist signals/suggestions, audit trail), 3.3 UI (connect-AWS flow + least-privilege /
CloudFormation handout + suggestion review→confirm into manifest). Roadmap beyond AWS:
same `connectors.base.Connector` interface for GCP / Azure / GitHub, etc.

To resume: read this file's Progress Log (section C) bottom-up + memories
[[complisense-phase1-readiness]], [[complisense-engine-gaps]]. Propose Phase 3 sub-features
one at a time and wait for go.

---

## A. END-TO-END AUDIT FINDINGS (2026-06-26, read-only, nothing changed)

Audited by 4 parallel read-only agents across: root `.md` docs, compliance engine +
rulepacks, legal-grounding/safety docs, backend + landing page. Mapped to the four
appendices: Grounding (primary sources), Liability/Disclaimer/Accuracy-Safety,
Legal-Correctness Mechanics (Addendum), and the "scan end-to-end" instruction.

### HIGH — legal/liability exposure

- [ ] **H1** `agent/scoring/overall.py:8` — `verdict_from_score()` returns
  "PARTIALLY COMPLIANT" (compliance-determination language). Must be readiness
  language. *(Liability §1)*
- [ ] **H2** `rulepacks/*.yaml` (ALL) — no `applicability` block on any rule. Engine
  flags non-SDF startups for SDF-only duties (DPIA/audit/DPO). False-flags the ICP.
  *(Addendum §2)*
- [ ] **H3** `rulepacks/*.yaml` (ALL) — no dual-layer citations
  (`act_citation`+`rule_citation`), no `source_url`, `status`, `enforcement_date`,
  `date_status`, `verification`. Bare "Section 5"/"Art.9" only. *(Grounding §1,
  Addendum §1)*
- [ ] **H4** `LEGAL_REVIEW_NEEDED.md` — MISSING. Mandated living checklist +
  per-pack reviewer sign-off absent. No auditable "reviewed by counsel" state.
  *(Grounding §E, Liability §8)*
- [ ] **H5** `euai_core_v1.yaml` (updated 2025-08-24, ~306 days stale) — pre-dates
  Digital Omnibus (7 May 2026). Risk: hardcodes EU high-risk 2 Aug 2026 instead of
  `provisional_pending_amendment` ~Dec 2027. *(Addendum §3)*
- [ ] **H6** `agent/evaluators/file_presence.py`, `keyword_check.py`,
  `schema_validate.py` — gameable: pass on file existence / keyword-anywhere /
  field-presence. No value validation (email format, ISO date, threshold ranges).
  Verifies presence not substance. *(matches engine-gaps memory)*
- [ ] **H7** `saas/app/config.py:51` — hardcoded default
  `admin_api_token = "dev-admin-token"`; weak fallback guards
  `POST /api/v1/upload-scan`.

### MEDIUM

- [ ] **M1** Missing docs: `docs/SOURCES.md`, `docs/SOURCES_ACT.md`,
  `docs/DATA_HANDLING.md`, `docs/TERMS_NOTES.md`, `SECURITY.md`, root `LICENSE`.
  *(Grounding §A/§E, Liability §5/§7)*
- [ ] **M2** `docs/` untracked in git. `LEGAL_REFERENCE_DPDP_EUAI.md` (good,
  primary-sourced, EU date correct) lacks `version` + `last_verified`, no VC history.
- [ ] **M3** rulepacks pre-date `LEGAL_REFERENCE_DPDP_EUAI.md` by 29–306 days. 9
  Part-A.3 corrections (Rule 6 (a)–(g) not "7+MFA"; breach two-track clock; retention
  two-tier floor; SDF gating) NOT applied to packs.
- [ ] **M4** EU coverage ~10–13% (euai_core = 10 rules / 9 articles). Missing: Art 5
  prohibited practices, Art 6/Annex III high-risk classification, Art 50 transparency,
  role-gating (provider/deployer/importer/GPAI). *(Addendum §5)*
- [ ] **M5** `saas/app/distribution.py:263` — "without storing your data" but
  `findings_json` + `results_summary` stored in Mongo. Defensible (no raw artefacts)
  but undocumented → needs `DATA_HANDLING.md`.
- [ ] **M6** `landing-page/app/page.tsx:1075` — "ensure compliance" → readiness.
  Disclaimer buried in `/terms`, not on main site.
- [ ] **M7** `AGENT_ZIP_USAGE.md:136` — contradicts 3 docs: claims scanner scans
  model binaries (.pkl/.onnx/.pt); others say docs-only.
- [ ] **M8** Findings carry no `enforcement_date` in UI. DPDP phased to ~May 2027
  shown as urgent fails → false "violation today" impression. *(Liability §2)*

### LOW — doc hygiene (NO deletions without user ok)

- [ ] **L1** Duplicate root `.md`: `ARCHITECTURE_DECISION` vs `ARCHITECTURE_CLARIFICATION`;
  `PHASE_STATUS` vs `ALL_FIXES_AND_STATUS`; 4× FIXES files. See
  `REDUNDANT_FILES_TO_REMOVE.md` (not acted on).
- [ ] **L2** `ANALYSIS_AND_ROADMAP.md:290` growth projections undated, no baseline.
- [ ] **L3** `COMPLETE_IMPLEMENTATION_SUMMARY.md:49` points to legacy `scanner_enhanced.py`.
- [ ] **L4** Landing testimonials = generic placeholders ("Media Platform"/"Fintech");
  confirm intent (not fake logos).

### CLEAN (verified OK)

JWT auth (no leaked secrets / no tokens in logs) · raw artefact content NOT uploaded ·
no fake customer logos/traction · public readiness tool correctly absent (it is Phase 1) ·
`LEGAL_REFERENCE_DPDP_EUAI.md` EU date + DPDP dual-cite logic correct **in the reference**
(just not propagated to packs).

---

## B. RECOMMENDED BUILD ORDER

### PHASE 0 — Foundation (correctness scaffolding; the appendices). Build FIRST.

Rationale: Phase 1 captures applicability facts and consumes applicability-gated,
cited rules. Build the spine before the product on top of it.

- [x] **0.1 Rulepack schema v2** — add `applicability` block, dual citations
  (`act_citation`/`rule_citation` + `source_url`), `status`, `enforcement_date`,
  `date_status`, `verification`, `current_as_of`, per-pack `reviewer`/`review_status`
  + "pending professional legal review" note. JSON-schema validator. Stay
  complykit-format-compatible. *(closes H3, parts of H2/H4/M2)*
- [x] **0.2 Engine applicability gating** — scanner resolves each rule's
  `applicability` against an entity profile; non-applicable → `not_applicable`, never
  `fail`. *(closes H2)*
- [x] **0.3 Propagate legal corrections** — apply the 9 Part-A.3 fixes to DPDP packs;
  set EU high-risk to `provisional_pending_amendment` ~Dec 2027; refresh euai packs.
  *(closes H5, M3; starts M4)*
- [x] **0.4 Grounding + safety docs** — `SOURCES.md`, `SOURCES_ACT.md` (STOP for
  review per grounding rule), `LEGAL_REVIEW_NEEDED.md`, `DATA_HANDLING.md`,
  `TERMS_NOTES.md`, `SECURITY.md`, `LICENSE`; commit `docs/`. *(closes H4, M1, M5)*
- [x] **0.5 Honesty quick-wins** — readiness verdict language; surface
  `status`/`enforcement_date` in output; landing disclaimer + "ensure readiness";
  admin-token hardening. *(closes H1, H7, M6, M8)*
- [x] **0.6 Engine substance hardening** — value validation (email/date/threshold
  formats, semantic context) to reduce gameability. *(closes H6)*

### PHASES 1–8 — product capabilities (per CLAUDE.md, unchanged order)

- [x] **Phase 1** Tier-0 Guided Manifest + public DPDP Readiness Score (no-login)
  - [x] 1.1 Manifest model + questionnaire (`compliance/manifest.py`) → applicability profile
  - [x] 1.2 Readiness scoring engine (`compliance/readiness.py`) — unknown ≠ ready
  - [x] 1.3 Public no-login API (`saas/app/readiness.py`) — anonymous teaser vs signed-in full
  - [x] 1.4 Public web page (`landing-page/app/readiness/`) — questionnaire → score → signup gate
  - [x] 1.5 Persistence + auth gating — consented signed-in storage; anonymous ephemeral
  - [x] 1.6 First-party analytics (`saas/app/analytics.py`) + DATA_HANDLING.md update
- [x] **Phase 2** Continuous monitoring, scan history & drift detection
  - [x] 2.1 Scan history (no-overwrite) — immutable `scan_runs` per project + posture score
  - [x] 2.2 Drift core (`compliance/drift.py`) + `/projects/{id}/monitoring/{history,drift,summary}`
  - [x] 2.3 Dashboard posture-over-time / trend UI (`monitoring.html` + `/projects/{id}/monitoring`)
  - [x] 2.4 Schedule + regression/overdue alerts + cron sweep (`monitoring_cron.py`, render cron)
- [~] **Phase 3** Tier-1 Connector Discovery (AWS, read-only least-privilege)
  - [x] 3.1 Connector framework + signal model + **4 read-only connectors** (AWS via STS
    assume-role/boto3; GCP, Azure, GitHub via bearer-token REST) + registry +
    least-privilege policy per provider + provider-agnostic signal→manifest-suggestion mapper
  - [ ] 3.2 API endpoints (run discovery, return suggestions, consent-gated persist + audit) + STS wiring
  - [ ] 3.3 UI: connect-AWS flow + least-privilege/CloudFormation handout + suggestion review→confirm
- [ ] **Phase 4** Tier-2 PII / Data-Flow Inference (human-in-the-loop)
- [ ] **Phase 5** Auto-updating rules: regulatory-change watcher (human-gated)
- [ ] **Phase 6** MCP server for CompliSense
- [ ] **Phase 7** LLM Remediation Copilot (local/consent data path)
- [ ] **Phase 8** Regulator-ready evidence exports + multi-team roles

---

## C. PROGRESS LOG (append one line per completed feature)

- 2026-06-27 — **Phase 2.3 + 2.4 done — PHASE 2 COMPLETE.** 2.3 trend UI:
  `saas/templates/monitoring.html` (Chart.js posture-over-time + drift tables +
  alerts + schedule selector; client-fetches the monitoring JSON API), page route
  `GET /projects/{id}/monitoring` (main.py) + "Monitoring" link on reports.html.
  2.4 schedule + alerts: per-project `monitoring_schedule` (off/daily/weekly/monthly)
  via `GET/PUT /projects/{id}/monitoring/schedule`; `monitor_alerts` collection +
  `create_alert` (dedupe on open) + `list_alerts`/`acknowledge_alert` endpoints;
  **regression alerts raised inline** in `record_scan_run` when a new scan drifts
  backwards (high if a high-severity rule regressed); `evaluate_overdue_scans` sweep +
  `saas/app/monitoring_cron.py` entrypoint + Render `cron` service (daily 06:00 UTC) for
  scan-overdue alerts. Indexes for `monitor_alerts` (database.py). Tests: +12
  (test_monitoring_api.py now 20). Full suite: **124 passed, 0 failed.**
- 2026-06-27 — **Phase 3.1 done.** Tier-1 connector framework + AWS read-only discovery.
  Decisions (confirmed with user): access = cross-account **STS AssumeRole**; persist
  **signals + suggestions only, consent-gated** (never creds/raw payloads/ARNs). New
  `connectors/` package: `base.py` (`DiscoveredSignal`, `Suggestion`, `Connector` ABC —
  pure, dep-free), `aws.py` (`AWSConnector`: boto3-OPTIONAL/lazy + injectable
  `client_factory`; assume-role once, reuse temp creds; 9 read-only probes — CloudTrail,
  S3 enc/PAB/lifecycle/location, IAM MFA, GuardDuty, Config, KMS, RDS, Backup, region;
  each probe defensively wrapped → one failure degrades a single signal, not the scan;
  `least_privilege_policy()` = Get/List/Describe only), `mapping.py`
  (`signals_to_suggestions` → manifest answer suggestions: storage_locations,
  has_security_safeguards [confirm when enc+logging+access all present, else review],
  retention_defined, cross_border_transfer [review]; honest — PII/consent NOT inferred).
  Suggestions are proposals, never auto-applied. Tests: +8 (`test_connectors_aws.py`,
  fake client_factory, no boto3/network).
  **Multi-connector (same session):** added `gcp.py`, `azure.py`, `github.py` — all
  real over bearer-token REST via an injectable `http_get` (default = `requests`; tests
  inject a fake router, no SDK/network), emitting the SAME normalized signal keys so one
  mapper serves every provider. `connectors/registry.py` (`get_connector(provider, **kw)`
  + `available_providers` + `CONNECTOR_REQUIREMENTS`). Each connector ships a per-provider
  least-privilege doc (AWS IAM JSON, GCP role/perms, Azure Reader, GitHub fine-grained
  read scopes). Tests: +11 (`test_connectors_more.py`). NEXT in Phase 3: 3.2 API endpoints
  (run discovery + consent-gated persist + audit) + per-provider credential wiring, 3.3 UI.
- 2026-06-27 — **Phase 2.1 + 2.2 backend foundation done.** Continuous monitoring spine.
  `compliance/drift.py` (pure): `rule_states_from_findings` (compact snapshot, no raw
  artefact text), `posture_score` (0-100 over applicable rules; None when none applicable,
  no fake 0), `compute_drift` (regressions/improvements/added/removed/NA-transitions +
  score_delta; PARTIAL ranks between FAIL/MISSING and PASS; NA flips never count as
  drift). `saas/app/monitoring.py`: `record_scan_run` appends an immutable `scan_runs`
  history doc on completion + read API `/projects/{id}/monitoring/{history,drift,summary}`.
  Hooked into BOTH completion paths in `distribution.py` (`/agent/results`,
  `/api/v1/upload-scan`) — best-effort, never breaks upload. `scan_runs` indexes added
  (database.py); router wired in main.py. History is additive (no overwrite) so re-running
  a scan_id preserves the timeline. Tests: +18 (`test_drift.py` 10, `test_monitoring_api.py`
  8). Full suite: **112 passed, 0 failed.** NEXT in Phase 2: 2.3 trend UI, 2.4 cron+alerts.
- 2026-06-26 — End-to-end audit complete; this plan written. No code changed.
- 2026-06-26 — **0.1 done.** Added `compliance/rulepack_schema.py` (v2 validator), wired
  validation into `agent/rules/loader.py` (non-fatal warn; `strict`/`RULEPACK_STRICT`),
  populated all 4 packs with applicability + dual citations + status/enforcement/date_status/
  verification + pack-level review metadata. Tests: `tests/test_rulepack_schema.py` (14 pass).
  EU packs set to `provisional_pending_amendment` ~2027-12-02 (Omnibus), not 2 Aug 2026.
  NOTE: euai_core and euai_extended are byte-identical content — flagged for 0.3 dedup.
- 2026-06-26 — **0.2 done.** Added `compliance/applicability.py` (resolve_applicability +
  default_profile). Wired into `agent/scanner.py`: `run_scan(..., entity_profile=None)` —
  non-applicable rules → `NOT_APPLICABLE` status + `not_applicable` count, evaluator skipped.
  Result dicts now pass through citations/legal_status/enforcement_date/date_status/
  verification. Profile None = gating inactive (backward compatible). Tests:
  `tests/test_applicability.py` (9). Suite: 23 pass.
- 2026-06-26 — **0.3 done.** EU date corrections already applied in 0.1. Resolved the
  euai_core==euai_extended duplication: extended is now a true superset — added 4 LIVE-now
  EU rules (Art 5 prohibited, Art 4 literacy, Art 50 transparency, Arts 53-55 GPAI),
  role-gated + correctly dated (in_force vs phased). Pack rule counts: dpdp_core 7,
  dpdp_extended 13, euai_core 10, euai_extended 14.
- 2026-06-26 — **0.4 done.** Created `LEGAL_REVIEW_NEEDED.md` (generated from packs;
  per-rule review checklist + non-primary flags), `docs/SOURCES.md`, `docs/SOURCES_ACT.md`
  (DRAFT, Act pending primary-text verification), `docs/DATA_HANDLING.md`,
  `docs/TERMS_NOTES.md`, `SECURITY.md`, root `LICENSE` (proprietary; complykit stays
  Apache-2.0). Added `version`/`last_verified` to LEGAL_REFERENCE.
- 2026-06-26 — **0.5 done.** `agent/scoring/overall.py`: verdict now readiness language
  ("PARTIALLY READY — GAPS IDENTIFIED", never "COMPLIANT") + `readiness_framing()` helper.
  `saas/app/config.py`: weak default secrets (admin token, jwt) now WARN in dev, RAISE in
  production (H7); render.yaml already provisions both. Landing: "ensure compliance" →
  readiness; added "not legal advice" footer disclaimer. Tests: `test_readiness_language.py`.
- 2026-06-26 — **0.6 done.** `agent/evaluators/file_presence.py`: present-but-empty /
  placeholder values ("TODO"/"changeme"/blank) now count as MISSING; optional typed
  `field_validations` (email/iso_date/url/min_length) — wired `grievance_contact: email`
  into DPDP notice rules. Scanner surfaces `invalid_fields`. Tests:
  `test_substance_hardening.py`. End-to-end sample scan: 5 PASS + SDF/Children correctly
  NOT_APPLICABLE for a default startup.
- 2026-06-26 — **POST-PHASE-0 CLEANUP (user-requested).**
  - Fixed the 3 pre-existing test failures at root cause: `render_pdf` now accepts the
    legacy 2-arg form + synthesizes safe assessment defaults + `ChainableUndefined` so
    optional/NA fields render blank (also fixed the genuinely broken `api_handlers.py`
    2-arg caller); `test_cli` rewritten against the real `agent.cli` click group;
    `test_scanner_enhanced` mock made realistic (`exists: True`).
  - Gameability gap 3: `schema_validate` no longer returns blanket coverage=1.0 — measures
    substantive field population. Gap 5: `techdoc_coverage` scales the explicit-doc score
    by how populated the doc is (empty `{}` model card no longer earns full credit).
  - Gap 4: added `compliance/cross_document.py` — advisory, opt-in cross-document
    consistency checks (never affects pass/fail). Wired into `run_scan(consistency_checks=)`.
  - EU coverage (M4): added high-risk classification (Art 6/Annex III), conformity + CE
    marking (Arts 43/47-48), EU-database registration (Art 49), post-market monitoring
    (Arts 72-73). Pack counts now: dpdp_core 7, dpdp_extended 13, euai_core 14,
    euai_extended 18.
  - Report UI: audit PDF template now shows a "Citation &amp; readiness" column (act+rule
    citations, "prepare by {date}" vs "enforceable now", provisional flag, verification
    badge with ⚠ for non-primary) and NOT_APPLICABLE rows; surfaces `invalid_fields`.
  - Tests: 66 pass (added cross_document + evaluator-substance tests). Full suite GREEN
    (no `--ignore` needed anymore).
- 2026-06-27 — **Phase 1 follow-ups (user-requested).**
  - Admin-gated `GET /api/v1/readiness/analytics/summary`: now requires `X-Admin-Api-Token`
    (new `require_admin` dep in `saas/app/readiness.py`), not just any signed-in user.
    Tests added (reject missing/bad token, accept valid).
  - Discoverability: added `/readiness` to the landing nav (desktop `site-nav` + mobile
    menu) so the public tool isn't an orphan page. `landing/.env.example` documents
    `NEXT_PUBLIC_API_BASE_URL` / `NEXT_PUBLIC_APP_BASE_URL`. Landing typechecks clean.
  - (The "untracked files" note was a `git add` reminder for staging — no code change.)
- 2026-06-27 — **PHASE 1 COMPLETE.** Tier-0 Guided Manifest + public DPDP Readiness Score.
  1.1 `compliance/manifest.py` (questionnaire + Manifest + `manifest_to_profile` →
  applicability gate; Third-Schedule trigger logic). 1.2 `compliance/readiness.py`
  (score_manifest reuses v2 packs + gating; unknown counts as gap, never silently ready;
  each gap carries citation + readiness framing). 1.3 `saas/app/readiness.py` public router
  (`/api/v1/readiness/questionnaire`, `/score`) — anonymous = score + top-3 teaser +
  ephemeral; signed-in = full report. 1.4 `landing-page/app/readiness/` (client tool →
  score → signup gate; "answers not stored" notice; typechecks clean). 1.5 persistence
  (`readiness_assessments`, consent-gated, anonymous never stored) + list/get endpoints.
  1.6 `saas/app/analytics.py` first-party non-PII funnel (`readiness_completed`, `signup`)
  + admin summary; DATA_HANDLING.md §3 updated to built reality. Tests: +26 (manifest 7,
  readiness 6, readiness_api 10, analytics 3). Full suite: **92 passed, 0 failed.**
  NOTE: marketing site change only visible after `npm run build` / Vercel redeploy. New
  page reads `NEXT_PUBLIC_API_BASE_URL` (defaults to prod backend).
- 2026-06-26 — **PHASE 0 COMPLETE.** New tests: 35 pass (schema/applicability/readiness/
  substance). Full suite: 53 pass, 2 fail + 1 collection error — ALL THREE PRE-EXISTING on
  the clean base (test_cli `cli.cli` attr, test_render `render_pdf()` signature,
  test_scanner_enhanced threshold). Phase 0 added zero new failures. Pre-existing failures
  left untouched (not in Phase-0 scope; flagged here for a future cleanup pass).
