# CompliSense-AI – Plans & Tiers

This document describes the four planned pricing tiers and how they map to features and the current codebase.

## 1. Overview

- **Free** – 10 scans/month; core EU AI Act checks; basic dashboards.
- **Standard** – Unlimited scans (TBD); remediation guidance; extended rules; basic history (Mongo-backed).
- **Premium** – Advanced evaluators (bias, explainability, drift); team features; rich analytics.
- **Premium+** – Enterprise: SSO, multi-tenant, private rulepacks, on-prem/VPC, SLAs, white-glove remediation.

Only the **Free** tier is currently fully wired into the product (scan limits, visible tier labels). The others are modeled in configuration and documentation as roadmap items.

---

## 2. Tier Details

### 2.1 Free (Implemented)

- **Intended users**: Individual developers, small teams evaluating the product, accelerators.
- **Limits**:
  - Up to **10 scans per month** per user (enforced server-side).
  - Up to ~2 active projects (configurable later).
- **What they see**:
  - Overall compliance percentage.
  - Artifact compliance (which key documents exist vs. missing).
  - List of failed/partial rules with status, risk, and limited evidence.
- **What they do not get**:
  - Deep remediation guidance for every rule.
  - Long-term history and analytics.
  - Advanced evaluators (bias, explainability, drift).

**Code hooks**:

- Enforcement of 10 scans/month:
  - `saas/app/projects.py` → `create_scan_configuration` checks monthly count for `tier == "free"`.
- UI exposure:
  - `saas/app/main.py` → `/api/stats` returns `user_tier`, `free_scans_used`, `free_scans_limit`.
  - `saas/templates/user_dashboard.html` shows current tier and free scan usage.
- Plan configuration:
  - `saas/app/plans.py` → `PLANS["free"]`.

---

### 2.2 Standard (Planned)

- **Intended users**: Teams actively working toward EU AI Act readiness.
- **Limits**:
  - Planned: higher or unlimited scans/month; more projects (TBD in code).
- **Features (beyond Free)**:
  - Step-by-step remediation guidance for each failed or partial rule.
  - Extended rule coverage for:
    - Art. 12 – conformity assessment support.
    - Art. 17 – post-market monitoring.
    - Art. 19 – extended record-keeping and logging.
  - Basic history & comparison in dashboard:
    - Relies on MongoDB to store scan summaries.
  - Email notifications when scans complete.

**Status**: defined in `saas/app/plans.py` with TODO markers; wiring into UI and enforcement to be added after MVP.

---

### 2.3 Premium (Planned)

- **Intended users**: Organizations with higher regulatory exposure or portfolio of high-risk systems.
- **Features (beyond Standard)**:
  - Advanced evaluators:
    - Bias / fairness evaluator.
    - Explainability / interpretability evaluator.
    - Performance drift and robustness checks.
  - Team / role-based access control:
    - Projects and scans scoped by team roles.
  - Rich analytics and trend dashboards:
    - Time series of compliance scores and artifact coverage.
    - Breakdown by article, risk level, and project.

**Status**: Conceptual design only; evaluator stubs and RBAC hooks are future work.

---

### 2.4 Premium+ (Enterprise, Planned)

- **Intended users**: Enterprise buyers with strong regulatory and contractual requirements.
- **Features (beyond Premium)**:
  - Multi-tenant SaaS, SSO, detailed audit logs across tenants.
  - Custom rule authoring & private rulepacks:
    - Internal policies and sector-specific rules.
  - On-prem / VPC deployments:
    - For highly regulated sectors.
  - SLAs, dedicated support, and “compliance co-pilot” services:
    - Helping fix gaps, not just identify them.

**Status**: Strategy-level; technical hooks include:
  - Modular rulepacks.
  - Mongo-based audit logs (`agent/db/mongo.py`).
  - Planned RBAC and multi-tenant layers in the SaaS app.

---

## 3. Implementation Notes

### 3.1 MongoDB Placement

- For **Free**:
  - MongoDB is optional; users can run the system entirely without it.
  - Any MongoDB-backed functionality is strictly additive.
- For **Standard+**:
  - MongoDB becomes a core dependency for:
    - Scan history and comparison.
    - Analytics and dashboards.
    - Audit logging (who ran what, when, under which rulepack).

### 3.2 `.pkl` / Binary Scanning

- **Free**:
  - Does **not** scan `.pkl` / model binaries.
  - Focuses purely on documentation and governance artifacts.
- **Standard / Premium**:
  - Roadmap includes optional evaluators that introspect models for:
    - Schema/architecture consistency with documentation.
    - Basic health and robustness checks.
- Decisions around model-file scanning will carefully balance:
  - Security & privacy.
  - Complexity of supporting multiple frameworks.
  - Actual regulatory demand.

---

## 4. MVP Status

- **Free** tier:
  - Implemented and enforced (10 scans/month).
  - UI shows tier and usage.
  - Docs and messaging aligned.
- **Standard / Premium / Premium+**:
  - Modeled in `saas/app/plans.py`.
  - Documented here as the roadmap.
  - Implementation intentionally deferred until the core product has real usage and feedback.

