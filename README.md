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

Building steps for ClientModule (local agent):

1. SaaS Web Dashboard 

- FastAPI Backend (saas/app/main.py)
  * Web server with CORS support 
  * Static file serving 
  * Template rendering 
  * Basic API endpoints

- Authentication System (saas/app/auth.py)
  * User registration/login 
  * JWT token generation 
  * Protected routes 
  * Session management

- Web Interface (saas/templates/dashboard.html)
  - Responsive Bootstrap UI 
  - Stats dashboard 
  - Feature cards 
  - Modal forms

2. Project Management System

   - Create, read, update, delete projects 
   - Project-specific configurations 
   - Scan configuration management 
   - User isolation (users only see their own projects)

3. Agent Generation Service

   - Dynamic agent creation per scan configuration 
   - Customized main scripts with project-specific settings 
   - Cross-platform support (Windows, macOS, Linux)
   - Integration with existing TruthModule

4. Secure Distribution System 

   - Protected download endpoints 
   - Agent customization based on user/project 
   - Heartbeat and results reporting 
   - Status tracking

5. Enhanced User Dashboard

   - Project management interface 
   - Scan configuration workflow 
   - Agent download with project selection 
   - Real-time statistics

Workflow:

- Register/Login
- Create a project 
- Configure a scan 
- Download the customized agent 
- Run the agent locally

Step-by-Step Guide for Clients
Step 1: Extract and Set Up
bash
# Extract the downloaded agent
unzip complisense_agent_YOUR_SCAN_ID.zip -d complisense_agent
cd complisense_agent

# Set up the environment (Linux/macOS)
chmod +x setup_agent.sh
./setup_agent.sh

# Or on Windows, just double-click: setup_agent.bat
Step 2: Activate the Environment
bash
# Linux/macOS
source complisense_env/bin/activate

# Windows
complisense_env\Scripts\activate.bat
Step 3: Run the Scan (THIS IS THE KEY PART)
bash
# Basic scan - replace "/path/to/your/ml/model" with your actual model path
python3 run_scan.py --project-path /Users/hardikgoel/Downloads/complisense_AI/model_2mb.pkl --output-dir ./scan_results
Step 4: Find Your Results
After scanning, check the output directory (default: ./complisense_output or your specified --output-dir) for:

compliance_findings.json - Detailed results

scan_summary.txt - Summary report

Starting uvicorn server for flask [After implementing JWT and other security considerations relating to pem keys]:

export ADMIN_API_TOKEN="dev-token-123" [MAYBE Optional]
uvicorn server.saas_api:app --reload --port 8080

building agent:

pyinstaller \
  --onefile \
  --windowed \
  --name CompliSenseAgent \
  agent/agent_ui.py


running agent:

python3 -m agent.agent_ui

What client will choose as input:

/ml-project/
 ├── model/
 │   ├── model.pkl
 │   ├── model_card.json
 ├── data/
 │   ├── dataset.csv
 │   ├── dataset_card.json
 ├── training/
 │   ├── train.py
 ├── configs/
 │   ├── config.yaml


run (Dev testing): 

python3 -m agent.agent_ui

Confidence Scoring Framework (0–100%)
Core idea

Every EU AI obligation gets:

Evidence signals

Weights

Confidence score

New concept

Each rule returns signals, not just pass/fail.

rm -rf build dist

Rebuilding app:

pyinstaller CompliSenseAgent.spec --clean  [IF MEA... Issue occurs or only use this to generate .pkg]

pyinstaller --onefile --windowed --name CompliSenseAgent agent/agent_ui.py
or pyinstaller CompliSenseAgent.spec

zip -r dist/CompliSenseAgent-macos.zip dist/CompliSenseAgent.app

if you want your dev to bypass apple app run, 
xattr -dr com.apple.quarantine CompliSenseAgent.app

issue in signing the app for now, therefore open through this:
./dist/CompliSenseAgent.app/Contents/MacOS/CompliSenseAgent

if you get this error: 

(venv) hardikgoel@192 CompliSense-AI % ./dist/CompliSenseAgent.app/Contents/MacOS/CompliSenseAgent

urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
macOS 15 (1507) or later required, have instead 15 (1506) !
zsh: abort      ./dist/CompliSenseAgent.app/Contents/MacOS/CompliSenseAgent


Just run source 3.10_venv/bin/activate
export MACOSX_DEPLOYMENT_TARGET=15.6


📜 License

MIT License TODO

💡 Built with love to make AI safer, compliant, and trustworthy.