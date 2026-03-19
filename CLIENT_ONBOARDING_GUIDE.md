# CompliSense-AI – Client Onboarding & How-To Guide

## 1. What This Tool Does (In One Sentence)

**CompliSense-AI helps you assess how well your AI system’s documentation and governance artifacts align with selected provisions of the EU AI Act.**

It is a **technical compliance support tool** – it does **not** replace legal advice.

---

## 2. High-Level Flow (What to Expect)

1. **Create a project** in the SaaS dashboard (name, model type, industry).
2. **Configure a scan**:
   - Choose which EU AI Act rulepack to use (e.g. `euai_core_v1`, `euai_extended_v1`).
   - Choose output formats (PDF, JSON, HTML).
3. **Download your customized local agent** from the dashboard.
4. **Run the agent locally** on your own infrastructure:
   - Point it at the root folder of your AI project.
   - Choose an output folder for reports.
5. **Review reports**:
   - PDF “audit report” with compliance percentages, risks, and evidence.
   - JSON payload for integration.
   - SaaS dashboard view (selected metadata only – scores, counts, statuses).

No training data, model weights, or raw logs are uploaded by default – only high‑level **scan metadata** if you opt-in to SaaS features.

---

## 3. Required Artifacts (What Files Should You Have?)

To get meaningful results, you should have a few key governance artifacts in your project directory.

These are **strongly recommended**, not strictly required (the scanner will still run, but you will see missing‑artifact warnings if they are absent).

### 3.1 Core Governance Artifacts

| File | Purpose | EU AI Act Articles |
|------|---------|--------------------|
| `risk_register.yaml` | Central list of identified risks, severities, mitigations, and statuses for your AI system. | Art. 9 (Risk Management) |
| `model_card.json` | Technical documentation for the model: purpose, architecture, training data summary, limitations, evaluation metrics, etc. | Art. 11 (Technical Documentation), Art. 13 (Transparency) |
| `dataset_card.json` | Documentation for the dataset(s): sources, preprocessing, representativeness, known limitations, bias mitigation, etc. | Art. 10 (Data Governance) |

**If these files are missing**:

- The scan will **still complete**, but related rules will be flagged as:
  - `MISSING` or `FAIL`, reducing your compliance percentage.
  - The PDF will explicitly state which artifacts are missing under:
    - “Required EU AI Act Artifacts”
    - “Why This System Is Not Compliant”.

This mirrors real‑world compliance expectations: if you do not have risk registers, model cards, or dataset documentation, you are not compliant with those governance aspects.

---

## 4. What the Scanner Looks At (Free Tier)

In the **Free tier**, the local agent focuses on:

- **Presence and basic validity** of the artifacts above.
- **Schema conformance** (e.g. does your risk register have required fields).
- **Coverage scores** for documentation (how complete the docs are).
- **Rule evaluation** for a curated subset of EU AI Act provisions:
  - Art. 9 – Risk Management
  - Art. 10 – Data Governance
  - Art. 11 – Technical Documentation
  - Art. 13 – Transparency
  - Art. 14 – Human Oversight
  - Art. 15 – Accuracy & Robustness (basics)
  - Art. 20 – Record Keeping (core logging expectations)

**Free tier does _not_**:

- Load or analyze `.pkl` / `.onnx` / model binaries.
- Perform deep bias/fairness analysis or explainability checks.
- Store detailed results in a central database – only optional metadata is sent to SaaS.

Those appear in higher tiers (see Plan/Tier section).

---

## 5. Running the Local Agent – Step by Step

### 5.1 From SaaS Dashboard

1. Log in to `CompliSense-AI`.
2. Create a project and scan configuration.
3. Download the customized agent zip (e.g. `complisense_agent_scan_xxxxx.zip`).

### 5.2 On Your Machine

```bash
unzip complisense_agent_scan_xxxxx.zip
cd complisense_agent_scan_xxxxx

# Setup (first time)
./setup_agent.sh          # macOS / Linux
# or
setup_agent.bat           # Windows

# Activate virtualenv
source complisense_env/bin/activate      # macOS / Linux
# or
complisense_env\\Scripts\\activate.bat   # Windows

# Run a scan against your project folder
python run_scan.py --project-path /path/to/your/project --output-dir ./results
```

You will see console output plus:

- `results/compliance_findings.json`
- `results/compliance_report.pdf`

If SaaS integration is enabled in that agent config, a **summary** (scores, counts, statuses) will also be posted to your dashboard.

---

## 6. What Stakeholders See in Reports

### 6.1 For Engineering & Compliance Teams

- **Overall compliance percentage**.
- **Artifact compliance**: how many key documents are present versus missing.
- **Per‑rule findings**:
  - Status: PASS / PARTIAL / FAIL / MISSING.
  - Confidence and risk level.
  - Evidence (which files, coverage, missing fields, validation issues).
  - Recommended remediation actions (in higher tiers).

### 6.2 For VCs and Non‑Technical Stakeholders

- One‑page executive summary:
  - Overall score.
  - Key missing artifacts.
  - Top non‑compliant rules.
- Narrative around:
  - “We have a structured, automated EU AI Act readiness assessment.”
  - “We track our risk registers, model cards, and dataset documentation centrally.”
  - “We can show progress over time as we close gaps.”

This is exactly what early‑stage investors (including YC‑style programs) want to see:
**a credible, repeatable process** around compliance, not perfection.

---

## 7. Tiers & What Clients Get

### Free

- Up to **10 scans/month** (all projects combined).
- Core EU AI Act checks (selected rules for Arts. 9, 10, 11, 13, 14, 15, 20).
- Local agent + basic SaaS dashboard.
- See:
  - Compliance percentage.
  - List of issues / failed rules.
  - Which key artifacts are missing.

### Standard  _(planned)_

- Everything in Free, plus:
- Step‑by‑step remediation guidance for improving coverage and compliance.
- More detailed rule coverage for Arts. 12, 17, 19 (extended logging, monitoring).
- Basic history and comparison in the dashboard (MongoDB‑backed).
- Email notifications on scan completion.

### Premium  _(planned)_

- Everything in Standard, plus:
- Advanced evaluators:
  - Bias / fairness evaluator.
  - Explainability checker.
  - Performance drift / robustness checks.
- Role‑based access (teams).
- Rich analytics and trend dashboards.

### Premium+ (Enterprise)  _(planned)_

- Everything in Premium, plus:
- Multi‑tenant SaaS, SSO, detailed audit logs.
- Custom rule authoring and private rulepacks.
- On‑prem / VPC deployments.
- SLAs, dedicated support.
- White‑glove remediation support: we help you fix gaps, not just highlight them.

For now, only the **Free** tier is fully enforced in code (scan limits, feature set). Higher tiers are modeled in configuration and documentation as the roadmap.

---

## 8. Data Handling & Privacy (For Clients & VCs)

### Local Agent

- Runs entirely on your infrastructure.
- Reads:
  - Project directory structure.
  - Governance artifacts (risk register, model card, dataset card, etc.).
- Produces:
  - Local JSON & PDF files stored where you choose.

### SaaS Platform

- Receives **metadata only**, such as:
  - Scan ID, project ID, user ID.
  - Timestamps (created, started, completed).
  - Aggregate summary (e.g. number of passed/failed rules, overall score).
- Does **not** ingest:
  - Raw training data.
  - Model weights / binaries.
  - Full logs or intermediate artifacts (unless you explicitly add that in a future enterprise feature).

### Legal Positioning

- All UIs and reports clearly state:
  - This is **not legal advice**.
  - It **helps assess alignment** with selected EU AI Act provisions.
  - Final legal interpretation and regulatory decisions remain with your legal/compliance teams.

---

## 9. Terminology Cheat‑Sheet

- **Rulepack**: Versioned set of rules mapping EU AI Act clauses to machine‑readable checks.
- **Evaluator**: Python modules that interpret artifacts (e.g. `file_presence`, `schema_validate`, `techdoc_coverage`).
- **Artifact**: A document or file that supports compliance (risk register, model card, dataset card, policies, logs).
- **Assessment**: Combined view of overall compliance %, artifact compliance, and rule outcomes.
- **Tier**: Subscription level (Free, Standard, Premium, Premium+), controlling limits and features.

---

## 10. Quick FAQ

**Q: Do I need all three files (`risk_register.yaml`, `model_card.json`, `dataset_card.json`) to run a scan?**  
**A:** No. The scan will still run, but missing artifacts will be clearly highlighted and will lower your compliance score for the associated articles.

**Q: Does CompliSense-AI read or upload my training data or model weights?**  
**A:** No. The local agent only reads your project structure and governance artifacts. The SaaS server receives only metadata (scores, counts, timestamps) to power dashboards.

**Q: Can I extend rules for internal policies or other regulations?**  
**A:** Yes. The system is rule‑based; you can add additional YAML rulepacks for internal controls or other frameworks (e.g. ISO, NIST) in higher tiers.

**Q: Is this enough to claim “EU AI Act compliant”?**  
**A:** No tool alone can make that guarantee. CompliSense-AI is designed to support your compliance program by making gaps visible, not to replace legal counsel.

---

This guide is intended to be a one‑stop, self‑serve document for new clients, internal stakeholders, and early‑stage investors (YC‑style) to quickly understand how to use CompliSense‑AI and what to expect from it.

