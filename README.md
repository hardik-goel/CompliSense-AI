# CompliSense-AI
Smart compliance insights that detect, guide, and fix AI risks—without storing your data.

Why CompliSense-AI?

The EU AI Act and upcoming regulations worldwide place strict compliance obligations on companies using AI.
Non-compliance can mean heavy fines, reputational risk, or blocked deployments.

CompliSense-AI is a hybrid agent + SaaS platform that:

Runs locally in client infrastructure (no sensitive data leaves)

Scans ML pipelines, datasets, and models against legal obligations

Generates audit-ready reports (JSON/PDF)

Scales into guided remediation and automated fixes

Features

✅ Local-first Agent — privacy-preserving compliance scans
✅ Rule Engine — maps EU AI Act obligations → testable checks
✅ Audit Reports — JSON + PDF outputs, ready for regulators
✅ CLI & API — use via terminal or integrate into pipelines
✅ Extendable — add new rulepacks for other jurisdictions (US, ISO, etc.)
✅ Premium Roadmap — remediation guides + auto-fix in GitHub (agentic AI)

This project is divided into two modules. 

TruthModule = The core compliance engine (your existing code)
ClientModule = The user-facing interface that runs locally on client machines

Architecture

                    ┌───────────────────────────────┐
                    │            SaaS Layer          │
                    │  - Dashboard (future)          │
                    │  - Rulepack updates            │
                    │  - User/Org management         │
                    │  - Report archival             │
                    └───────────────▲────────────────┘
                                    │
                   Rulepack updates │ Compliance summaries
                                    │
       ┌────────────────────────────┴────────────────────────────┐
       │                   Local Agent (this repo)               │
       │  - CLI & FastAPI API                                    │
       │  - Evaluators (schema_validate, file_presence, etc.)    │
       │  - Rule Engine (py-rule-engine)                         │
       │  - Report Generator (Jinja2 + WeasyPrint)               │
       │  - Artefact Scanner (model cards, dataset cards, risks) │
       └────────────────────────────▲────────────────────────────┘
                                    │
                    Project artefacts│ (kept inside client system)
                                    │
     ┌──────────────────────────────┴────────────────────────────┐
     │     ML Models, Datasets, Docs (compliance evidence)       │
     │  e.g., model_card.json, dataset_card.json, risk_register  │
     └───────────────────────────────────────────────────────────┘

Project structure:

```CompliSense-AI/
│
├── agent/                      # core package
│   ├── __init__.py
│   ├── scanner.py              # runs evaluators + rules
│   ├── rules/
│   │   ├── __init__.py
│   │   └── loader.py           # load rulepacks
│   ├── report/
│   │   ├── __init__.py
│   │   ├── render.py           # Jinja2 + WeasyPrint renderer
│   │   └── templates/
│   │       └── audit_report.html.j2
│   └── evaluators/             # pluggable checks (planned)
│
├── cli.py                      # Click CLI entrypoint
├── rulepacks/                  # rule definitions (EU AI Act v1)
│   └── euai_core_v1.yaml
├── artefacts/                  # sample artefacts for testing
│   ├── compliance/risk_register.yaml
│   ├── schemas/risk_register.schema.json
│   ├── data/dataset_card.json
│   └── model/model_card.json
│
├── tests/                      # pytest unit tests
│   ├── test_loader.py
│   ├── test_scanner.py
│   ├── test_render.py
│   └── test_cli.py
│
├── pytest.ini                  # pytest configuration
└── README.md                   # this file
```

Code Flow:

1. CLI 

```python cli.py scan --root artefacts --pack rulepacks/euai_core_v1.yaml --out out```

2. Rulepack Loading

loader.py loads YAML rules → list of obligations (Art. 9, 10, 11).

3. Scan Execution

* scanner.py runs evaluators (e.g., file_presence, schema_validate).

* Context dict built per rule (exists? schema_valid? missing_fields?).

* Expression (e.g. exists and missing_fields == 0) evaluated by rule_engine.

4. Results Aggregation

Summary + detailed results stored in findings.json.

5. Report Generation

render.py renders audit_report.pdf with Jinja2 + WeasyPrint.

6. (Optional API)

uvicorn agent.api:app runs the same logic behind an HTTP endpoint.

[TODO]

Testing

Uses pytest with pytest-cov for coverage reporting.

Test suite covers:

Rulepack loading

Scanner logic with mocked evaluators

Report rendering

CLI command execution

Run tests with coverage:

pytest -v

Generate HTML coverage report:

pytest --cov=agent --cov=cli --cov-report=html
open htmlcov/index.html


Example Run:

### Run scan
```python3 -m agent.cli scan --root artefacts --pack rulepacks/euai_core_v1.yaml --out out```

## Outputs:
### - out/findings.json
### - out/audit_report.pdf

sample_findings.json:

```
{
  "summary": {"passed": 2, "failed": 1},
  "results": [
    {
      "rule_id": "EUAI-ART9-RISK-MGMT-001",
      "clause": "Art.9",
      "title": "Risk management system documented",
      "status": "FAIL",
      "context": {"schema_valid": true, "coverage": 0.0}
    }
  ]
}
```

Roadmap

```commandline
 EU AI Act (Arts 9–11) rulepack

 CLI scans & PDF reports

 Unit tests + coverage

 Add more evaluators (bias checks, explainability)

 API endpoints for remote triggering

 SaaS dashboard with multi-tenant org support

 Remediation suggestions in premium tier

 Auto-fix + GitHub PR (agentic AI co-pilot)
```

TO RUN:

python3 -m agent.cli scan \
  --root artefacts \
  --pack rulepacks/euai_core_v1.yaml \
  --out out \
  --mongo \
  --mongo-uri mongodb://localhost:27017 \
  --mongo-db complisense \
  --mongo-coll findings_

fire up mongodb : [EITHER OR ALL]

mongod --config /usr/local/etc/mongod.conf
mongod
mongosh

CLIENT JOURNEY:
1. Client visits your SaaS dashboard (web)
2. Client configures scan (model path, custom requirements via chat)
3. Client downloads **customized agent** for their specific scan
4. Agent runs locally (no data leaves their system)
5. Results sync back to SaaS dashboard (anonymized metadata only)
6. Client views beautiful reports in web dashboard

To run the dashboard:

cd saas/app
python3 main.py
http://0.0.0.0:8000/

![img.png](img.png)

📜 License

MIT License TODO

💡 Built with love to make AI safer, compliant, and trustworthy.