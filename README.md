# CompliSense-AI

CompliSense-AI is a local-agent plus SaaS compliance platform for scanning project artefacts against configurable regulatory rulepacks.

The codebase now supports multiple packs side by side. Today that includes:

- `euai_core_v1`
- `euai_extended_v1`
- `dpdp_india_core_v1`
- `dpdp_india_extended_v1`

The architecture is intentionally additive. EU support is still present, and India-first operation is handled through configuration rather than by removing EU logic.

Desktop app now supports:

- selecting a rulepack directly before running a scan
- opening dedicated DPDP and EU experience URLs (`COMPLISENSE_DPDP_URL`, `COMPLISENSE_EU_URL`)

## What The Product Does

- runs evidence collection locally on the client machine
- evaluates artefacts against a selected rulepack
- produces findings and remediation
- syncs scan metadata and findings to a hosted SaaS dashboard
- keeps the engine extendable for new markets such as UK, India, or sector-specific overlays

## Current Rulepack Model

Rulepacks are registered in:

- [compliance/registry.py](compliance/registry.py)

They are exposed to the SaaS UI through:

- `GET /api/rulepacks`

The dashboard UI loads the full catalog, so both EU and DPDP packs should be visible in the scan configuration UI.

Each rulepack can also specify its own artifact manifest via `required_artifacts_manifest`, so EU and DPDP evidence coverage is scored independently.

## Configuration-Driven Market Focus

The default pack is controlled by environment variable:

```env
DEFAULT_RULEPACK_ID=dpdp_india_core_v1
```

That means:

- if you want India-first behavior, set `DEFAULT_RULEPACK_ID=dpdp_india_core_v1` or `dpdp_india_extended_v1`
- if you want EU-first behavior, set `DEFAULT_RULEPACK_ID=euai_core_v1` or `euai_extended_v1`

This changes:

- default selected rulepack in the UI
- default compliance program in project creation
- default local agent pack when a pack is not explicitly chosen

It does **not** remove the other packs from the product. They remain available in the UI and through the CLI.

## Project Structure

```text
CompliSense-AI/
├── agent/                         # local agent, scanner, evaluators, reporting
├── compliance/                    # rulepack registry and market metadata
├── rulepacks/                     # executable compliance packs
├── artefacts/                     # EU sample artefacts
├── sample_artefacts/dpdp_india/   # DPDP sample artefacts
├── saas/                          # FastAPI SaaS templates and backend
├── landing-page/                  # Next.js landing page for Vercel
├── main.py                        # Render/FastAPI entrypoint
└── .env.example                   # deployment config example
```

## Supported Sample Artefact Roots

EU sample root:

- `artefacts`

DPDP sample root:

- `sample_artefacts/dpdp_india`

## Local Setup

Use the repo venv if you already have it:

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
source 3.10_venv/bin/activate
```

If you need a fresh environment:

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
python3.10 -m venv 3.10_venv
source 3.10_venv/bin/activate
pip install -r requirements.txt
```

## Run The SaaS Locally

This runs the FastAPI dashboard on `localhost:8000`.

### India-first local run

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
source 3.10_venv/bin/activate
export DEFAULT_RULEPACK_ID=dpdp_india_core_v1
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### EU-first local run

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
source 3.10_venv/bin/activate
export DEFAULT_RULEPACK_ID=euai_core_v1
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- `http://127.0.0.1:8000/`

What you should see:

- both EU and DPDP rulepacks available in the dashboard scan configuration
- the configured `DEFAULT_RULEPACK_ID` preselected by default

## Test The Rulepack Catalog Locally

With the SaaS running:

```bash
curl http://127.0.0.1:8000/api/rulepacks
```

You should see entries for:

- `euai_core_v1`
- `euai_extended_v1`
- `dpdp_india_core_v1`
- `dpdp_india_extended_v1`

The configured default pack will also be flagged in the response.

## Run Agent Scans Locally

### EU core sample

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
source 3.10_venv/bin/activate
python -m agent.cli scan \
  --root artefacts \
  --pack rulepacks/euai_core_v1.yaml \
  --out /tmp/euai_core_out \
  --no-pdf
```

### EU extended sample

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
source 3.10_venv/bin/activate
python -m agent.cli scan \
  --root artefacts \
  --pack rulepacks/euai_extended_v1.yaml \
  --out /tmp/euai_extended_out \
  --no-pdf
```

### DPDP core sample

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
source 3.10_venv/bin/activate
python -m agent.cli scan \
  --root sample_artefacts/dpdp_india \
  --pack rulepacks/dpdp_india_core_v1.yaml \
  --out /tmp/dpdp_core_out \
  --no-pdf
```

### DPDP extended sample

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
source 3.10_venv/bin/activate
python -m agent.cli scan \
  --root sample_artefacts/dpdp_india \
  --pack rulepacks/dpdp_india_extended_v1.yaml \
  --out /tmp/dpdp_extended_out \
  --no-pdf
```

Outputs are written into the selected `--out` directory, especially:

- `findings.json`
- optionally `audit_report.pdf` if PDF rendering is enabled

## Run The Desktop Agent UI

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
source 3.10_venv/bin/activate
python -m agent.agent_ui
```

The UI now uses the configured default pack rather than a hardcoded EU pack.

## India-First Product Flow

1. Start the SaaS locally with `DEFAULT_RULEPACK_ID=dpdp_india_core_v1`
2. Register a user at `http://127.0.0.1:8000/`
3. Create a project
4. Confirm the compliance program defaults to DPDP
5. Configure a scan and confirm DPDP is preselected
6. Run a local DPDP sample scan against:
   - `sample_artefacts/dpdp_india`
7. Upload findings through the local or hosted flow
8. Review results in:
   - `/dashboard`
   - `/reports`

## Deployment

Backend entrypoint:

```bash
uvicorn main:app --host 0.0.0.0 --port 10000
```

Required environment variables:

```env
ENVIRONMENT=production
PORT=10000
MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/complisense?retryWrites=true&w=majority
MONGO_DB=complisense
DEFAULT_RULEPACK_ID=dpdp_india_core_v1
JWT_SECRET=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ADMIN_API_TOKEN=replace-with-a-long-random-agent-token
CORS_ORIGINS=https://your-render-service.onrender.com
LOG_LEVEL=INFO
SECURE_COOKIES=true
```

Recommended deployment split:

- Render: FastAPI backend
- MongoDB Atlas: persistence
- Vercel: `landing-page/`

## Agent Upload API

Endpoint:

`POST /api/v1/upload-scan`

Authentication:

- `Authorization: Bearer <jwt>`
- or `X-API-Key: <ADMIN_API_TOKEN>`

Example payload:

```json
{
  "project_id": "proj_12345678",
  "scan_summary": { "passed": 12, "failed": 2 },
  "findings_json": {
    "summary": { "passed": 12, "failed": 2 },
    "results": []
  },
  "timestamp": "2026-04-21T10:00:00Z",
  "scan_id": "scan_abcdef12",
  "scan_name": "Weekly compliance run",
  "rulepack_version": "dpdp_india_core_v1"
}
```

## Current DPDP Packs

### `dpdp_india_core_v1`

Starter checks for:

- notice
- consent
- safeguards
- breach register
- children’s data
- Significant Data Fiduciary basics
- grievance redressal

### `dpdp_india_extended_v1`

Adds:

- legitimate use register
- retention and erasure schedule
- access workflow
- correction/erasure request register
- processor inventory
- cross-border transfer posture

Roadmap document:

- [DPDP_EXTENDED_V1_ROADMAP.md](DPDP_EXTENDED_V1_ROADMAP.md)

## Notes

- The product is now configurable by rulepack, not locked to EU AI Act.
- EU support remains available.
- India-first operation is controlled by `DEFAULT_RULEPACK_ID`.
- Adding UK or another market should follow the same model:
  - add a rulepack
  - add sample artefacts
  - register it in `compliance/registry.py`
  - expose its legal/control metadata in the SaaS UI
