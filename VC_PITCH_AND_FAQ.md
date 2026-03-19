# CompliSense-AI – VC Briefing, Pitch & FAQ

This document is written for investors, accelerators (including YC‑style programs), and strategic partners who want to understand **what CompliSense‑AI is**, **why it matters**, and **how it is built**.

---

## 1. One‑Line Pitch

> **CompliSense‑AI is a hybrid local‑agent + SaaS platform that continuously checks an AI system’s documentation and governance artifacts against selected provisions of the EU AI Act, surfacing gaps, evidence, and remediation guidance.**

It lives where real compliance work happens: **inside the engineering workflow**, not as a one‑off PDF from an external consultant.

---

## 2. Problem & Why Now

1. The EU AI Act introduces **binding obligations** (risk management, data governance, documentation, transparency, oversight, logging, monitoring).
2. Engineering teams are already struggling to:
   - Map legal text to concrete artifacts (risk registers, model/dataset cards, logs).
   - Keep documentation aligned with fast‑moving code.
   - Prove to regulators, customers, and boards that they have a **systematic** approach.
3. Existing solutions are:
   - Consulting‑heavy, one‑off, and expensive.
   - Not embedded in developer workflows.
   - Often “slideware” rather than executable checks.

The EU AI Act is moving from concept to enforcement; companies will need **repeatable, automated, and auditable** ways to demonstrate alignment.

---

## 3. Solution – What CompliSense‑AI Does

### 3.1 Hybrid Architecture

- **Local Agent** (CLI / downloadable bundle)
  - Runs entirely on the client’s infrastructure.
  - Reads project structure and governance artifacts (risk registers, model cards, dataset docs).
  - Produces local JSON + PDF reports.

- **SaaS Dashboard**
  - Manages projects, scan configurations, and agent downloads.
  - Optionally receives **metadata only** (scan IDs, timestamps, aggregate scores, counts).
  - Provides history, trends, and high‑level analytics (in higher tiers).

### 3.2 What It Checks

- Presence and basic quality of core artifacts:
  - `risk_register.yaml` (Art. 9 – risk management system).
  - `model_card.json` (Art. 11 – technical documentation; Art. 13 – transparency).
  - `dataset_card.json` (Art. 10 – data governance).
- Schema and coverage:
  - Required fields present and non‑empty.
  - Coverage metrics and threshold checks.
- Rule‑based alignment with selected EU AI Act provisions:
  - Today: focus on Articles 9, 10, 11, 13, 14, 15 (core), 16, 18, 20.
  - Roadmap: Article 12, 17, 19 in more detail, plus downstream frameworks (ISO/NIST).

### 3.3 What the User Sees

- **Executive summary**:
  - Overall compliance percentage.
  - Artifact compliance (how many key documents are present).
  - Why the system is currently “not ready for audit”.
- **Per‑rule findings**:
  - PASS/PARTIAL/FAIL/MISSING, confidence, risk.
  - Evidence (which files, what coverage, missing fields, validation issues).
  - Remediation suggestions (Standard+ tiers).

---

## 4. Rules – Maintenance, Versioning, & EU AI Act Updates

### 4.1 Representation

- Rules are defined in **YAML rulepacks** (`rulepacks/euai_core_v1.yaml`, `euai_extended_v1.yaml`).
- Each rule encodes:
  - `id` – stable identifier (e.g. `EUAI-ART9-RISK-MGMT-001`).
  - `clause` – EU AI Act article reference.
  - `evaluator` – Python module (`file_presence`, `schema_validate`, `techdoc_coverage`, etc.).
  - `inputs` – configuration (paths, required fields, thresholds).
  - `expression` – boolean or score‑based logic.
  - `thresholds` – numeric thresholds for PASS/PARTIAL/FAIL.
  - `severity` – impact level (`Critical`, `Major`, etc.).

### 4.2 Versioning Strategy

- Each rulepack is **versioned semantically**, e.g.:
  - `euai_core_v1` → `euai_core_v1.1` → `euai_core_v2`, etc.
- Changes follow a clear policy:
  - Patch (`v1.0 → v1.0.1`): bugfixes, minor wording changes, no behavior change.
  - Minor (`v1.0 → v1.1`): new rules, relaxed/tightened thresholds, backward compatible.
  - Major (`v1.x → v2.0`): structural changes or new coverage model.
- Rulepacks live in Git with:
  - Code review for changes.
  - Change logs summarizing which clauses were added/updated and why.

### 4.3 Keeping up with EU AI Act Evolution

As guidance, standards, and enforcement practice evolve, we update rulepacks by:

1. Tracking **official guidance** (e.g. delegated acts, regulator Q&A, ENISA/ISO mappings).
2. Mapping new expectations to:
   - Updated schemas (e.g. richer risk register fields).
   - New evaluators (e.g. for log retention, post‑market monitoring).
   - Additional rules (e.g. more granular checks under Art. 12, 17, 19).
3. Releasing **new rulepack versions** while keeping older ones available:
   - Clients can pin to a rulepack version for reproducibility.
   - Enterprise tiers can maintain **private rulepacks** for internal policies.

At the product level, this becomes a **recurring value**: we ship updated rulepacks aligned with regulatory practice, not just one static “v1.0”.

---

## 5. Data Handling & Legal Positioning

### 5.1 Data Flows

- **Local agent**:
  - Reads project files and governance artifacts.
  - Never sends raw data or model weights by default.
  - Outputs reports to local disk.

- **SaaS**:
  - Receives only:
    - Scan ID, project ID, user ID.
    - Timestamps (created, started, completed).
    - Summary counts (number of passed/failed rules, overall scores).
  - Stores them in MongoDB (in Standard+ tiers) for history and analytics.
  - Uses an audit log collection to track:
    - Who ran which scan, when, under which rulepack, and with what (high‑level) status.

### 5.2 Legal & Messaging

Across PDF reports and the SaaS UI we explicitly state:

- CompliSense‑AI is a **technical compliance support tool**.
- It **does not provide legal advice** and is not a substitute for legal counsel.
- It **helps assess alignment** with selected EU AI Act provisions based on the artifacts supplied.

This framing:

- Reduces legal risk.
- Aligns expectations with what the tool can and cannot do.
- Resonates with legal/compliance teams, who can treat it as a **systematic lens** rather than an oracle.

---

## 6. Tiers & Monetization Strategy

### Free

- 10 scans/month.
- Core EU AI Act checks for key articles (9, 10, 11, 13, 14, 15 basics, 20).
- Local agent + basic SaaS dashboard.
- Shows issues and compliance percentage, but limited remediation depth.

### Standard  _(Roadmap – code placeholders exist)_

- Everything in Free.
- Detailed remediation steps and guidance for improving coverage and compliance.
- Wider rule coverage (Arts. 12, 17, 19).
- Basic history and comparison (Mongo‑backed).
- Email notifications.

### Premium  _(Roadmap)_

- Everything in Standard.
- Advanced evaluators:
  - Bias / fairness.
  - Explainability.
  - Performance drift / robustness.
- Team features and role‑based access.
- Rich analytics and trend visualizations.

### Premium+ (Enterprise)  _(Roadmap)_

- Everything in Premium.
- Multi‑tenant SaaS, SSO, extended audit logs.
- Custom rule authoring & private rulepacks.
- On‑prem / VPC deployments.
- SLAs, support, “compliance co‑pilot” services (help fixing, not just finding).

The codebase already has:

- A **plans module** with these tiers modeled.
- Free tier limits enforced (10 scans/month).
- Clear points where Standard+ features will be plugged in (MongoDB, analytics, evaluators).

---

## 7. Tech Architecture (Short Version)

- **Backend**: FastAPI (Python), modular routers for auth, projects, agent distribution.
- **Local Agent**:
  - Core scanner, evaluators, report generators.
  - Packaged agent bundles via an `AgentGenerator` service.
  - Roadmap/specs for PyInstaller‑based compiled binaries to protect rule logic.
- **Rule Engine**: YAML rulepacks + `py-rule-engine` for expression evaluation.
- **DB**: MongoDB (optional today, core in Standard+ tiers) for:
  - Scan results (findings).
  - Audit logs (per‑scan events).
- **Frontend**: HTML templates + Bootstrap, small JS layer for SPA‑like dashboard.

The architecture is deliberately simple and pragmatic, optimized for quick iteration with clear extension points for enterprise features.

---

## 8. Competitive Angle

1. **Developer‑first, local‑first**: Meets teams where they are (repos, CI, local infra), rather than requiring full data upload.
2. **Rule‑driven & explainable**: Every finding is tied to a rule, evidence, and (eventually) remediation, not a black‑box “risk score”.
3. **EU AI Act‑specific, but extensible**: Starting with EU AI Act, designed to layer in ISO/NIST, sectoral guidance, and internal policies.
4. **Built for iteration**: Rules and evaluators are modular, versioned, and testable.

---

## 9. FAQ (For VCs & Technical Evaluators)

**Q: How hard would it be to add another regulation (e.g. ISO 42001, NIST AI RMF)?**  
**A:** Low‑medium effort: add new rulepacks and evaluators; reuse the same scanner and reporting pipeline. The architecture is regulation‑agnostic at the core.

**Q: What stops someone from copying your rules?**  
**A:** For MVP/dev, rules are readable YAML. For production, we ship compiled binaries (PyInstaller) where rulepacks are bundled as resources and only surfaced via IDs, titles, and outcomes. The value is in the maintained rule library + platform, not just static YAML.

**Q: How do you keep rulepacks in sync with evolving guidance?**  
**A:** Through semantic versioning, Git‑based change control, and a deliberate policy for mapping new regulatory expectations to new or updated rules with clear changelogs.

**Q: What is the biggest technical risk?**  
**A:** Over‑fitting rules to today’s interpretation of the EU AI Act. Mitigated by:
  - Keeping rulepacks versioned and upgradable.
  - Designing evaluators to be composable.
  - Surfacing evidence and remediation so humans stay in the loop.

**Q: What is the biggest go‑to‑market risk?**  
**A:** Selling into compliance budgets vs. AI/ML budgets. Mitigated by:
  - Framing as a tool that reduces risk for both legal and engineering.
  - Strong story for B2B SaaS: dashboards, history, analytics.

---

## 10. Short Pitch Script (Founder Voice)

> “The EU AI Act is landing, and every serious AI team is going to need a repeatable way to show they’re aligned with it – not just a PDF from a consultant once a year.  
>  
> CompliSense‑AI is a local‑first agent plus a SaaS dashboard that reads your AI project’s governance artifacts – risk registers, model cards, dataset docs – and continuously checks them against a curated set of EU AI Act rules.  
>  
> We don’t ask you to upload your training data or models; everything heavy happens on your infrastructure, and we only collect the metadata needed for dashboards and history.  
>  
> For engineers, it’s a concrete list of what’s missing and how to fix it. For legal and leadership, it’s a living, auditable picture of where you stand against the regulation. For us as a business, it’s rulepacks and analytics that we can keep upgrading as the law – and the market – evolves.”  

