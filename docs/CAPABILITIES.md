# CompliSense-AI — what it supports (one page)

A regulatory **readiness** platform for **India DPDP** and the **EU AI Act**. It tells a team
how *ready* they are — with citations and "prepare-by" framing. **Not legal advice; no
compliance determination.** Rulepacks are **pending professional legal review**.

## The flow, end to end
1. **Declare** — answer a short Tier-0 questionnaire (applicability + posture) → a manifest.
2. **Discover** *(optional)* — connect AWS / GCP / Azure / GitHub read-only; signals become
   manifest *suggestions* you confirm. Infer PII categories from field **names** (never values).
3. **Score** — applicability/role-gated readiness; each gap carries its citation + enforcement date.
4. **Monitor** — every scan is kept; posture-over-time + drift/regression alerts; scheduled re-scan reminders.
5. **Record** — a **ROPA** (Record of Processing Activities) + a **data-flow diagram**, built
   **deterministically** from your declared processing activities, the names-only data-flow map
   and your questionnaire answers. Never AI-drafted — a register is facts, and a fabricated
   record is worse than a missing one. Fields we cannot source are stamped `UNKNOWN` and listed
   with how to fill them, so the register never over-claims. Marks the India trust boundary when
   personal data leaves the country. Every stage is badged with the **eight DPDPA domains**
   that apply to it, and the legend records the domains ruled *out* by your profile.
   `compliance/ropa.py`, `compliance/dfd.py`, `compliance/domains.py`.
6. **Stay current** — every generated artefact is stamped with the rulepack + rules it was
   built from (legally-material fields only). `fresh` / `review` / `stale` per document, with
   the changed field named. Pending regulatory-watch findings raise an early warning *before*
   any rule is edited. Nothing regenerates itself, and the monitoring cron raises
   `artefact_stale` / `regwatch_exposure` alerts so the client is told rather than having to
   ask. `compliance/provenance.py`, `saas/app/freshness_api.py`.
7. **Remediate** — an AI copilot explains a gap or drafts a document (grounded, consent-gated, "DRAFT — requires legal review").
   - **Generate artefacts** *(no documents yet?)* — for each gap, see where the artefact can be sourced
     (connector / questionnaire / AI draft / manual), AI-draft it, **explicitly approve** each one,
     then **download the approved set as a zip** to drop into the scan input folder. We can auto-fetch
     facts only from the connectors (AWS/GCP/Azure/GitHub) — everything else is your answers, an
     approved AI draft, or material only you can provide.
   - **Collect existing artefacts** *(agent-side)* — declare where docs live (**S3 · GCS · Azure Blob ·
     GitHub · Notion · Google Drive · SharePoint · local folder**); the downloaded agent reads them with
     your **local** credentials, classifies each with Claude (deterministic fallback) incl. **PDF/DOCX**,
     and stages the likely artefacts to scan. Contents never leave your machine; only non-secret config
     is stored. `agent/collectors/`, `collect_sources.py`.
8. **Govern** — assign a gap to a member; a **DPO signs it off**; every action audited.
9. **Export** — a regulator-ready, citation-backed evidence pack (JSON / HTML).

## Both regulations, end to end
| | India DPDP | EU AI Act |
|---|---|---|
| Applicability gating | SDF · Third-Schedule class · children · consent-manager · state | provider / deployer / GPAI role · EU-output trigger · open-source exemption |
| Posture scoring | ✅ full numeric score | ✅ role-gated numeric score (self-attested, **gated behind legal review**) |
| Citations + enforcement dates | ✅ (some Act cites DRAFT) | ✅ (secondary-sourced) · provisional dates flagged |

Surfaced in: the **public tool** (pick DPDP or EU), **project readiness**, the **MCP server**,
and the **evidence export**.

## Capabilities at a glance
- **Engine** — rulepack v2 (dual citations, applicability, enforcement dates, verification signal); readiness scoring; "unknown = gap" (never fabricates readiness).
- **Connectors** — read-only least-privilege discovery: AWS (STS), GCP/Azure/GitHub (REST). Credentials never stored.
- **PII / data-flow** — categories + cross-border, from field names only, human-confirmed.
- **ROPA + data-flow diagram** — deterministic register and SVG diagram from the same facts, so the table and the picture can never disagree. Completeness is reported honestly (unknowns listed, never guessed). Supports (does not close) DPDP s.5 / s.7 / s.8 / s.16.
- **DPDPA domain lens** — the eight domains buyers already read, as a *proven view* over the rulepack: a test fails if a rule belongs to no domain, or a domain has no backing rule.
- **Regulatory-change watcher** — hashes the cited legal sources; raises a **human-gated** review item on change (never auto-edits a rule).
- **Artefact freshness** — provenance stamps + staleness (`fresh`/`review`/`stale`) join the watcher to the documents a client is holding, so "we monitor the law" is a benefit they receive, not a backlog we keep. Surfaced as scheduled alerts, not only on request.
- **Records & currency page** — `/projects/{id}/records`: the register, the diagram, the domain rollup, the freshness report, and the form for declaring processing activities.
- **MCP server** — 8 read-only tools for Claude Desktop (rules, readiness, PII, connector policies).
- **Copilot** — Anthropic-backed, grounded in the cited rule + non-PII facts, consent-gated, drafts marked "requires legal review".
- **Teams / RBAC** — viewer · engineer · DPO · admin · owner; gap assignment + DPO sign-off, audited.
- **Evidence export** — timestamped pack with readiness, posture history, discovery/PII summaries, citations, governance — summaries only (no creds/raw/PII values).

## What it does NOT do
Not legal advice · rulepacks not lawyer-reviewed yet · verifies declared facts not real-world
truth · discovery is metadata-only (no values) · no offline LLM path · watcher detects but
doesn't decide · scanning runs client-side (overdue *alerts*, not forced scans) · external
integrations are fake-tested here, not run against real accounts.

> Deeper detail: [`README.md`](../README.md) · legal source of truth:
> [`docs/LEGAL_REFERENCE_DPDP_EUAI.md`](LEGAL_REFERENCE_DPDP_EUAI.md) · open review items:
> [`LEGAL_REVIEW_NEEDED.md`](../LEGAL_REVIEW_NEEDED.md) · data flows: [`docs/DATA_HANDLING.md`](DATA_HANDLING.md).

> Why the product is built this way — and what each choice costs — is recorded in
> [`docs/adr/`](adr/README.md) (13 decision records, structure enforced by `tests/test_adr.py`).
