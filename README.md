# CompliSense-AI

CompliSense-AI is a regulatory **readiness** platform (FastAPI + MongoDB backend, a local
scanning agent, a Next.js landing page, and configurable rulepacks for India DPDP and the
EU AI Act). It helps a team assess and track how *ready* they are for a regulation — it is
**not legal advice and makes no compliance determination**. Findings are framed as
"prepare by \<date\>" readiness items, with citations and enforcement framing, never as
"violations."

> **Want the whole product on one page?** Read [`docs/CAPABILITIES.md`](docs/CAPABILITIES.md) — a
> short end-to-end overview of everything it supports.
>
> **Source of truth for all legal content:** [`docs/LEGAL_REFERENCE_DPDP_EUAI.md`](docs/LEGAL_REFERENCE_DPDP_EUAI.md)
> and [`docs/SOURCES_ACT.md`](docs/SOURCES_ACT.md). Rulepacks are **pending professional legal
> review** — see [`LEGAL_REVIEW_NEEDED.md`](LEGAL_REVIEW_NEEDED.md).

## Capabilities (build phases)

| # | Capability | Where |
|---|------------|-------|
| 0 | **Foundation** — rulepack schema v2 (dual citations, applicability blocks, enforcement dates, verification signals) + engine applicability-gating | `rulepacks/`, `compliance/rulepack_schema.py`, `compliance/applicability.py` |
| 1 | **Tier-0 manifest + public readiness score (DPDP + EU AI Act)** — no-login questionnaire → honest score; pick India DPDP or EU AI Act; teaser anonymous, full report on signup | `compliance/manifest.py`, `compliance/readiness.py`, `saas/app/readiness.py`, `landing-page/app/readiness/` |
| 2 | **Continuous monitoring** — immutable scan history, posture-over-time, drift/regression detection, alerts + cron | `compliance/drift.py`, `saas/app/monitoring.py`, `saas/app/monitoring_cron.py` |
| 3 | **Tier-1 connectors** — read-only least-privilege discovery (AWS/GCP/Azure/GitHub) → manifest *suggestions* (user confirms) | `connectors/`, `saas/app/connectors_api.py`, `saas/app/project_readiness.py` |
| 4 | **Tier-2 PII / data-flow inference** — infer categories from field **names only** (never values), human-in-the-loop | `compliance/pii.py`, `compliance/dataflow.py`, `saas/app/pii_api.py` |
| 5 | **Regulatory-change watcher** — hash watched legal sources, raise a **human-gated** review item on change (never auto-edits rules) | `compliance/regwatch.py`, `saas/app/regwatch_api.py`, `saas/app/regwatch_cron.py` |
| 6 | **MCP server** — exposes the grounded read-only engine as tools for Claude Desktop | `mcp_server/` |
| 7 | **LLM remediation copilot** — explains/drafts grounded in the cited rule + user facts, consent-gated, readiness-framed | `compliance/copilot.py`, `saas/app/copilot_api.py` |
| 8 | **Evidence exports + team roles + gap governance** — regulator-ready citation-backed pack (JSON/HTML) + RBAC (viewer/engineer/**DPO**/admin/owner) + per-gap assignment & DPO **sign-off**, audited | `compliance/evidence.py`, `saas/app/evidence_api.py`, `saas/app/rbac.py`, `saas/app/teams.py`, `saas/app/gaps_api.py` |

Both **India DPDP and the EU AI Act** are applicability/role-gated and posture-scored end to end
(public tool, project, MCP, evidence). EU AI Act scoring is role-gated and honest ("unknown = gap")
but remains **secondary-sourced and pending legal review** — see `LEGAL_REVIEW_NEEDED.md`.
A 30-second product teaser is on the homepage (`landing-page/public/teaser.html`).

## What it does NOT do (read this)

- **Not legal advice; no compliance determination.** Output is *readiness*, never "you are compliant."
- **Rulepacks are not lawyer-reviewed yet** (`LEGAL_REVIEW_NEEDED.md` is open; `docs/SOURCES_ACT.md` is DRAFT). The EU AI Act score is **self-attested** posture against secondary-sourced rules — gated behind that review.
- **The engine verifies declared facts and field-shape, not real-world truth** — a well-formed manifest that doesn't reflect reality can still score well.
- **Discovery is metadata-only.** Connectors are read-only and never remediate; PII inference reads column *names*, never data, so PII in generically-named fields or free text is invisible to it.
- **No fully-local/offline LLM path.** The copilot calls the Anthropic API (consent-gated, non-PII facts only); it drafts text and never changes your systems.
- **The watcher detects, it doesn't decide.** It flags source changes for a human; it does not auto-draft rule diffs or auto-version.
- **Scanning runs client-side.** The SaaS can't force a re-scan — "scheduled re-scans" raise an *overdue alert*, they don't execute a scan.
- **No live-cloud verification in this build.** Every external integration (AWS STS/boto3, GCP/Azure/GitHub REST, Anthropic, MCP, Mongo) is exercised via injected fakes in tests; none has been run against a real account/key here.

## Rulepacks

Registered in [`compliance/registry.py`](compliance/registry.py) and exposed via `GET /api/rulepacks`:

- `dpdp_india_core_v1`, `dpdp_india_extended_v1` (India DPDP)
- `euai_core_v1`, `euai_extended_v1` (EU AI Act)

The default pack is configuration-driven (does **not** remove the others):

```env
DEFAULT_RULEPACK_ID=dpdp_india_core_v1   # or euai_core_v1
```

## Project structure

```text
CompliSense-AI/
├── agent/            # local agent: scanner, evaluators, reporting, CLI
├── compliance/       # engine: registry, manifest, readiness, applicability, drift,
│                     #         pii, dataflow, regwatch, copilot, evidence
├── connectors/       # Tier-1 read-only discovery connectors (aws/gcp/azure/github)
├── mcp_server/       # MCP server (tools over the read-only engine)
├── rulepacks/        # executable compliance packs (DPDP + EU AI Act)
├── saas/             # FastAPI backend + Jinja templates
├── landing-page/     # Next.js marketing site + public readiness tool
├── docs/             # legal reference, sources, data handling, terms notes
├── main.py           # FastAPI entrypoint
└── .env.example
```

## Local setup

```bash
python3.11 -m venv 3.11_venv
source 3.11_venv/bin/activate
pip install -r requirements.txt
```

### Run the SaaS (FastAPI, :8000)

```bash
source 3.11_venv/bin/activate
export ENVIRONMENT=development
export MONGO_URI="mongodb://127.0.0.1:27017"   # or your Atlas URI
export MONGO_DB=complisense
export DEFAULT_RULEPACK_ID=dpdp_india_core_v1
export JWT_SECRET=dev-local-secret ADMIN_API_TOKEN=dev-local-admin
export SECURE_COOKIES=false COOKIE_DOMAIN=""    # host-only cookie so login works on localhost
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
# open http://127.0.0.1:8000/  ·  catalog: curl http://127.0.0.1:8000/api/rulepacks
```

> **Localhost login tip:** leave `COOKIE_DOMAIN=""`. The production default is
> `.complisenseai.com`, which the browser rejects on `localhost` — so login appears to fail
> ("Network error"). The app's API calls are same-origin, so no `API_BASE_URL` is needed locally.

### Run the landing page (Next.js, :3000)

```bash
cd landing-page && npm install && npm run dev
# public readiness tool at /readiness
```

### Run the tests

```bash
3.11_venv/bin/python -m pytest -q
# slow (~4min) due to weasyprint; for speed: -o addopts="" and target files
```

### MCP server (Claude Desktop)

```bash
python -m mcp_server.server   # stdio MCP server; see mcp_server/README.md for config
```

### Agent bundles (optional)

`make refresh-agent-bundles` rebuilds the compiled client CLI, clears cached ZIPs, and
validates all four rulepacks. Regenerate/download the agent ZIP from the SaaS afterwards
(old ZIPs can be stale). See the `Makefile` for `build-cli`, `smoke-cli-all`, etc.

## Selected API surface

| Area | Endpoint |
|------|----------|
| Public readiness | `POST /api/v1/readiness/score` (DPDP packs scored; EU packs role-gated, gated behind legal review) |
| Scan upload (agent) | `POST /api/v1/upload-scan` (Bearer JWT or `X-API-Key: ADMIN_API_TOKEN`) |
| Monitoring | `GET /projects/{id}/monitoring/{history,drift,summary}` |
| Connectors | `GET /api/v1/connectors`, `POST /projects/{id}/connectors/{provider}/discover` |
| Project readiness | `GET /projects/{id}/readiness` |
| PII / data flow | `POST /projects/{id}/pii/infer` |
| Reg-change watcher | `GET /api/v1/regwatch/{sources,changes}` (admin: `/run`, `/changes/{id}/review`) |
| Copilot | `POST /projects/{id}/copilot/remediate` (consent required) |
| Evidence export | `GET /projects/{id}/evidence`, `GET /projects/{id}/evidence/export.html` |
| Teams / roles | `POST /teams`, `POST /teams/{id}/members` (viewer/engineer/dpo/admin/owner), `POST /projects/{id}/team` |
| Gap governance | `POST /projects/{id}/gaps/{rule_id}/assign`, `POST /projects/{id}/gaps/{rule_id}/signoff` (DPO/admin), `GET /projects/{id}/gaps` |
| Teaser | `GET /teaser.html` (animated product teaser) |

Scheduled sweeps run as Render cron jobs: `monitoring_cron` (overdue/regression alerts) and
`regwatch_cron` (legal-source watch). See `render.yaml`.

## Deployment

Backend entrypoint: `uvicorn main:app --host 0.0.0.0 --port 10000`. Recommended split —
Render (FastAPI backend), MongoDB Atlas (persistence), Vercel (`landing-page/`).

Required env (see `.env.example`):

```env
ENVIRONMENT=production
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/complisense?retryWrites=true&w=majority
MONGO_DB=complisense
DEFAULT_RULEPACK_ID=dpdp_india_core_v1
JWT_SECRET=<long-random-secret>
ADMIN_API_TOKEN=<long-random-token>
APP_BASE_URL=...   API_BASE_URL=...   MARKETING_SITE_URL=...   CORS_ORIGINS=...
SECURE_COOKIES=true
```

> In production the backend **refuses to start** with the default `JWT_SECRET` / `ADMIN_API_TOKEN`
> — set strong values. Never commit secrets; rotate any that leak.

## DPDP packs

- **`dpdp_india_core_v1`** — notice, consent, safeguards, breach register, children's data, Significant Data Fiduciary basics, grievance redressal.
- **`dpdp_india_extended_v1`** — adds legitimate-use register, retention/erasure schedule, access workflow, correction/erasure register, processor inventory, cross-border posture.

Adding a market (e.g. UK): add a rulepack + sample artefacts, register it in
`compliance/registry.py`, and add its legal/control metadata — EU and DPDP support remain
available side by side.
