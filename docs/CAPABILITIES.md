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
5. **Remediate** — an AI copilot explains a gap or drafts a document (grounded, consent-gated, "DRAFT — requires legal review").
   - **Generate artefacts** *(no documents yet?)* — for each gap, see where the artefact can be sourced
     (connector / questionnaire / AI draft / manual), AI-draft it, **explicitly approve** each one,
     then **download the approved set as a zip** to drop into the scan input folder. We can auto-fetch
     facts only from the connectors (AWS/GCP/Azure/GitHub) — everything else is your answers, an
     approved AI draft, or material only you can provide.
   - **Collect existing artefacts** *(agent-side)* — point the local agent at a folder/repo; it
     classifies files with Claude (locally; deterministic fallback) and stages the likely
     artefacts into a folder to scan. Contents never leave your machine. `agent/collectors/`.
6. **Govern** — assign a gap to a member; a **DPO signs it off**; every action audited.
7. **Export** — a regulator-ready, citation-backed evidence pack (JSON / HTML).

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
- **Regulatory-change watcher** — hashes the cited legal sources; raises a **human-gated** review item on change (never auto-edits a rule).
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
