# CompliSense-AI — Final Audit & Verification Report

> **Read-only audit. Nothing was modified or deleted to produce this report.** Date: 2026-06-28.
> Method: 6 parallel read-only agents across Phases A–F, evidence cited as `file:line`.
> Source of truth for legal content: `docs/LEGAL_REFERENCE_DPDP_EUAI.md` + `docs/SOURCES_ACT.md`.

## 0. Verdict at a glance

| Phase | Area | Result |
|------|------|--------|
| B | Capabilities (9) | 5 PASS · 4 PARTIAL · 0 FAIL |
| C | Legal-correctness mechanics (9) | 6 PASS · 2 PARTIAL · 0 FAIL · 1 not-verifiable-vs-primary |
| D | Liability / safety (7) | 2 PASS · 3 PARTIAL · 2 FAIL |
| E | Security / hygiene (8) | 4 PASS · 3 PARTIAL · 1 FAIL |

No P0 *secret leak*. Two **unauthenticated state-mutation endpoints** and several **liability-surface gaps** are the most material findings.

---

## 1. Prioritised fix list

### P0 — Legal-correctness & liability (fix first)
1. **Copilot drafts are not stamped "draft — requires legal review"** *(D7, FAIL)* — `compliance/copilot.py:46,108-114`, `saas/app/copilot_api.py:94-118`. Generated document text carries only a generic disclaimer; the mandated marker is absent. Fix: stamp the marker into the drafted body + system prompt.
2. **`agent/report/dashboard.py:64-80` asserts compliance/violation** *(D2, PARTIAL→fix)* — "no immediate **high-risk violations were detected**" / "**does not meet the selected regulatory pack expectations**". Contradicts the readiness-only standard. Fix: reframe to readiness/gap language.
3. **SaaS scan-report HTML has no disclaimer** *(D1, FAIL surface)* — `saas/app/main.py:413-427,450-457` renders "Compliance Report" (Passed/Failed) with zero "not legal advice" line. Fix: add the disclaimer to both the `/html` and `/download` paths.
4. **`verification` signal dropped on public + dashboard surfaces** *(D3, PARTIAL)* — `landing-page/app/readiness/ReadinessTool.tsx:107-116` (field declared `:27`, never rendered) and all `saas/templates/*.html`. Uncertain (`secondary_source_only`) findings shown with equal authority. Fix: render verification + ⚠ badge as the agent report already does (`audit_report.html.j2:214`).
5. **DPDP Rule 8(1) class-based 3-yr erasure is not an enforced rule** *(C4/C5, PARTIAL)* — only prose in `dpdp_india_extended_v1.yaml:166`; `is_third_schedule_class` (`manifest.py:267`) and the `third_schedule_class_only` scope gate **nothing**. → add to `LEGAL_REVIEW_NEEDED.md` + encode as its own gated rule.
6. **EU packs are effectively un-scored** *(C7, PARTIAL — known scope gap)* — `manifest.py:271` hardcodes `"eu_roles": []`, so every `eu_provider`/`eu_gpai_provider` rule resolves NOT_APPLICABLE; open-source exemption is descriptive-only (no `is_open_source` flag, never tested in `applicability.py`). Engine + rulepack role/date tagging is correct (`euai_*` LIVE vs DEFERRED verified); the **EU manifest is not built**.
7. **`docs/DATA_HANDLING.md` omits three live data flows + public tool lacks a DPDP-grade privacy notice** *(D5, FAIL)* — undocumented: connector discovery persistence (`connectors_api.py:60`), PII inference persistence incl. field names (`pii_api.py:31-36`), and **live Anthropic egress** from the copilot (still labelled "Phase 7 — PLANNED" at `DATA_HANDLING.md:60` while `copilot.py:128-139` ships data to Anthropic). `landing-page/app/privacy/page.tsx` is a generic website policy, not a DPDP data-principal-rights notice for the readiness tool.

### P1 — Security
8. **Unauthenticated state mutation** *(E4, FAIL)* — `POST /agent/results` (`saas/app/distribution.py:182`) and `POST /agent/heartbeat` (`:165`) have **no auth**: any caller with a known/guessed `scan_id` can overwrite `findings_json`/`results_summary`/`status` and inject audit-log rows. Note: `POST /api/v1/upload-scan` **is** correctly authed (`_get_upload_actor`, `:74-88`). Fix: gate results/heartbeat behind the same admin-token/per-scan-token dependency.
9. **Hardcoded `/Users/hardikgoel/...` key paths read at import** *(E2, FAIL)* — `server/jwks.py:12-13` and `server/verify.py:7-8` crash on import anywhere but the author's laptop. They are **orphaned** (not imported by `saas/app/` or `main.py`). Fix: parameterise via env var or delete the `server/` package.
10. **`.env` is tracked by git** *(E1, hygiene)* — currently all secrets are commented out (no live leak, no rotation needed), but a future real value would auto-commit. Fix: `git rm --cached .env` (keep the local file; it's already in `.gitignore`).
11. **`dist/` (incl. a macOS app binary) and `.coverage` are committed despite being gitignored** — `git rm --cached` them.

### P2 — Feature/spec completeness (PARTIALs vs the original prompt)
12. **Regwatch is detection-only** *(B6)* — has watch-list, hashing, change-detection, human review queue + approve/dismiss + audit (`regwatch_api.py`). **Missing vs spec:** LLM-drafted proposed diff, plain-English summary, affected-**customers** mapping (only affected *rules*), version-bump-on-approval, customer change alert, export of approved diffs.
13. **MCP server** *(B7)* — 8 read-only tools exist (`mcp_server/tools.py:125`). **Missing vs spec:** `run scan`, `fetch findings`, `explain gap`; `list rule versions` is partial; and it is **standalone, not authenticated to a user account**, so it can't act on a specific user's data.
14. **Evidence + roles** *(B9)* — pack + RBAC + role-gated export work. **Missing vs spec:** per-gap **assignment**, **sign-off** workflow, `rulepack_version` in the pack, and audit-logging of team role changes (`teams.py`) and evidence exports (`evidence_api.py`) — both currently un-logged.

### P3 — Hygiene
15. **Unused/risky deps** — `python-jose==3.5.0` (+ `ecdsa`, Minerva timing issue) and `passlib==1.7.4` (unmaintained) are not imported anywhere; remove. Core web deps are current with no known open CVEs.
16. **Coverage metric misleads** — `pytest.ini --cov` measures only `agent`/`cli`, excluding `compliance/` and `saas/`. No test for `saas/app/distribution.py` (the module with the unauth endpoints). `compliance/registry.py` untested.
17. **Doc sprawl** — see §6 cleanup list (many stale `FIXES_*`/`*_SUMMARY`/architecture/scratch docs; `REDUNDANT_FILES_TO_REMOVE.md` is itself obsolete).

---

## 2. Phase B — Capabilities (PASS/PARTIAL with evidence)

| # | Capability | Verdict | Evidence / gap |
|---|-----------|---------|----------------|
| 1 | Tier-0 manifest | **PASS** | `manifest.py:234,262`; consumed at `readiness.py:85-87` |
| 2 | Public DPDP readiness tool | **PASS** | `readiness.py` teaser `:135`, signup-gate `:108`, consent persist `:117`, analytics `:90`; UI `ReadinessTool.tsx` |
| 3 | Monitoring / drift | **PASS** | `monitoring.py` record `:55`, history `:186`, drift `:203`, regression alert `:107`, overdue sweep `:393` + `monitoring_cron.py` |
| 4 | Tier-1 AWS connector | **PASS** | `connectors/aws.py` read-only policy `:30,271`; generic base/registry; creds dropped `connectors_api.py:122` |
| 5 | Tier-2 PII / data-flow | **PASS** | `pii.py:99` names-only; human-confirm `pii_api.py:132` |
| 6 | Reg-change watcher | **PARTIAL** | detection + review queue only; no LLM diff/summary/versioning/customer-alert/export |
| 7 | MCP server | **PARTIAL** | 8 read-only tools; no run-scan/fetch-findings/explain-gap; not user-authenticated |
| 8 | Remediation copilot | **PARTIAL** | grounded + consent + non-PII facts ✓; **no "draft — requires legal review" marker** |
| 9 | Evidence + roles | **PARTIAL** | pack + RBAC ✓; no gap-assignment, no sign-off, no rulepack_version, export/role-change not audited |

All 11 routers registered (`saas/app/main.py:66-95`); 244 tests collected and passing.

---

## 3. Phase C — Legal-correctness mechanics

| # | Item | Verdict | Note |
|---|------|---------|------|
| 1 | Dual citations; Act-level obligations cite the Act | **PASS** | children=Act s.9 (`dpdp_core:136`), rights ss.11-14 (`dpdp_ext:249-303`) |
| 2 | Rule 6 = Gazette (a)–(g), no MFA gloss | **PASS** | `dpdp_core:83`; no MFA/7-control hits |
| 3 | Breach Rule 7 = two tracks (72h to Board only) | **PASS** | `dpdp_core:112` |
| 4 | Retention = two obligations; 3-yr gated to classes | **PARTIAL** | one combined rule; 3-yr class rule not encoded as a gated rule |
| 5 | Applicability-gating at schema level; no over-flagging | **PASS** | SDF/children gates present; startup profile not flagged for DPO/DPIA |
| 6 | EU high-risk date provisional (Dec 2027), not 2 Aug 2026 | **PASS** | `euai_core:31-34`; the one `2026-08-02` is Art.50, correct |
| 7 | EU role-gating in the manifest | **PARTIAL** | packs correct; manifest hardcodes `eu_roles=[]`; OSS exemption non-actionable |
| 8 | Readiness-not-violation framing | **PASS** | `overall.py:13-31` |
| 9 | Citations match the reference (8/8 spot-checks) | **PASS** | no mismatches |

**Not verifiable against primary text (flagged, not guessed):** EU packs + several DPDP Act citations are `verification: secondary_source_only`; `docs/SOURCES_ACT.md` is DRAFT pending primary-text verification — already tracked correctly.

---

## 4. Phase D — Liability / safety

| # | Item | Verdict |
|---|------|---------|
| 1 | "Not legal advice" on every surface | **PARTIAL** — missing on SaaS scan-report HTML + several `saas/templates` |
| 2 | No "you are compliant" assertions | **PARTIAL** — `agent/report/dashboard.py:64-80` asserts violations/non-conformance |
| 3 | Per-rule `verification` surfaced | **PARTIAL** — dropped in public ReadinessTool + SaaS dashboard |
| 4 | LEGAL_REVIEW_NEEDED.md + per-pack sign-off | **PASS** |
| 5 | DATA_HANDLING.md covers every flow + DPDP privacy notice | **FAIL** — connectors/PII/copilot-egress undocumented; no DPDP notice for the tool |
| 6 | TERMS_NOTES.md as counsel checklist | **PASS** |
| 7 | Generated docs stamped "draft — requires legal review" | **FAIL** |

---

## 5. Phase E — Security / hygiene

| # | Item | Verdict |
|---|------|---------|
| 1 | Committed secrets | **PASS** (no live values) — but `.env` is tracked (hygiene) |
| 2 | Hardcoded local paths | **FAIL** — `server/jwks.py:12`, `server/verify.py:7` (orphaned, crash at import) |
| 3 | Connectors least-privilege & read-only | **PASS** — Get/List/Describe only; creds dropped |
| 4 | Auth on sensitive endpoints | **PARTIAL** — `upload-scan` authed ✓; `/agent/results` + `/agent/heartbeat` **unauth** ✗ |
| 5 | Production secret guards | **PASS** — `config.py:88-115` raises in prod on weak secrets |
| 6 | Tests for engine/rulepacks/applicability/features | **PARTIAL** — broad & green; `distribution.py` + `registry.py` untested; `--cov` excludes compliance/saas |
| 7 | Dependencies | **PARTIAL** — drop unused `python-jose`/`ecdsa`/`passlib`; core deps current |
| 8 | Open/paid boundary | **PASS** — `LICENSE` proprietary, complykit carved out as Apache-2.0 |

---

## 6. Phase F — Cleanup candidates (NOTHING DELETED — awaiting approval)

**Never delete (KEEP):** `docs/LEGAL_REFERENCE_*`, `docs/SOURCES*.md`, `LEGAL_REVIEW_NEEDED.md`, `docs/DATA_HANDLING.md`, `docs/TERMS_NOTES.md`, `LICENSE`, `SECURITY.md`, `README.md`, `.env.example`, `render.yaml`, `requirements.txt`, all `rulepacks/`, and source under `agent/ compliance/ connectors/ mcp_server/ saas/ tests/ landing-page/`.

### (1) Safe to delete — generated/duplicate/obsolete
| Path | Why | Tracked? |
|---|---|---|
| `dist/` | PyInstaller output, rebuildable, gitignored-but-committed | yes (`git rm --cached`) |
| `.coverage` | coverage data, generated | yes |
| `complisense_agent.log` | runtime log | yes |
| `img.png`, `img_1.png`, `img_2.png` | 3 byte-identical screenshots at root, unreferenced | yes |
| `REDUNDANT_FILES_TO_REMOVE.md` | lists files already deleted — self-obsolete | yes |
| `build/`, `htmlcov/`, caches, `.DS_Store` | generated, gitignored | no (disk only) |

### (2) Probably stale — confirm before deleting
- Status/changelog sprawl: `ALL_FIXES_AND_STATUS.md`, `FIXES_AND_PHASE_COMPLETION.md`, `FIXES_COMPLETE.md`, `FIXES_SUMMARY.md`, `QUICK_FIXES_SUMMARY.md`, `COMPLETE_IMPLEMENTATION_SUMMARY.md`, `PHASE_STATUS.md`, `IMPLEMENTATION_PLAN.md`, `ANALYSIS_AND_ROADMAP.md`, `ARCHITECTURE_CLARIFICATION.md`, `ARCHITECTURE_DECISION.md` (all tracked).
- Extensionless scratch notes: `explain` (tracked); `CODEX_ENDTOEND`, `NEXT_PHASEWISE_STEPS`, `TODO_NEXT_MAIN` (untracked).
- Orphaned `server/` package (`downloads.py`, `jwks.py`, `verify.py`, `static/`) — nothing imports it; not in render.yaml/Dockerfile.
- `testing_model/model.pkl` — unreferenced binary fixture.
- `venv-packager/pyvenv.cfg` (tracked venv artifact).
- Onboarding/pitch docs (`AGENT_ZIP_USAGE.md`, `MODEL_PATH_GUIDE.md`, `HOSTING_GUIDE.md`, `CLIENT_ONBOARDING_GUIDE.md`, `PLANS_AND_TIERS.md`, `VC_PITCH_AND_FAQ.md`) + `resources/docs/INDEX.md` — owner call (may still be wanted).
- Duplicate desktop-UI entrypoints (`agent/agent_ui.py` vs `agent_ui_enhanced.py` vs `agent_ui_launcher.py`) and overlapping artefact trees (`artefacts/` vs `sample_artefacts/` vs `passed artefacts/`) — confirm which are live fixtures.

### (3) Keep — everything else (source, current docs, `docs/BUILD_PLAN_AND_AUDIT.md`, `planning/`).

---

## 7. Intended-vs-built summary

| Item | Done | Partial | Missing |
|------|:----:|:-------:|:-------:|
| Tier-0 manifest | ✅ | | |
| Public readiness tool | ✅ | | |
| Monitoring / drift | ✅ | | |
| Tier-1 connectors (AWS+more) | ✅ | | |
| Tier-2 PII inference | ✅ | | |
| Reg-change watcher | | ⚠ detection-only | LLM diff, versioning, customer alert, export |
| MCP server | | ⚠ read-only tools | run-scan/fetch-findings/explain-gap, user auth |
| Remediation copilot | | ⚠ grounded+consent | "draft — requires legal review" marker |
| Evidence + roles | | ⚠ pack+RBAC | gap assignment, sign-off, rulepack_version, export/role audit |
| Legal-correctness mechanics | ✅ (6/9) | ⚠ retention rule, EU manifest | EU scoring end-to-end |
| Liability scaffolding | | ⚠ disclaimers/verification | draft marker, DATA_HANDLING coverage, DPDP tool notice |
| Security | ✅ (auth/secrets-guard/least-priv) | ⚠ tests/deps | auth on `/agent/results`+`/heartbeat`, drop hardcoded paths |

---

*End of audit. No files changed, nothing deleted. Awaiting approval before any cleanup.*
