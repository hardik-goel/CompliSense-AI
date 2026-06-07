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
source 3.11_venv/bin/activate
```

If you need a fresh environment:

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
python3.11 -m venv 3.11_venv
source 3.11_venv/bin/activate
pip install -r requirements.txt
```

If your venv was created against a removed Python install, recreate it.

## One-Command Bundle Refresh (Recommended)

To rebuild the compiled client CLI, clear cached generated ZIPs, and validate all four rulepacks in one go:

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
make refresh-agent-bundles
```

After this completes, generate/download the agent ZIP again from SaaS (old ZIPs can be stale).

Other useful commands:

```bash
make build-cli
make build-cli-clean
make clean-agent-cache
make smoke-cli-all
make smoke-cli-compiled
```

`make build-cli` is the default recommended build. Use `make build-cli-clean` only when you explicitly want a PyInstaller clean build.
`make smoke-cli-all` validates all four packs through `python -m agent.cli`.
`make smoke-cli-compiled` validates the frozen binary itself.

## Run The SaaS Locally

This runs the FastAPI dashboard on `localhost:8000`.

### Start local SaaS (single command flow)

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
source 3.11_venv/bin/activate
export DEFAULT_RULEPACK_ID=dpdp_india_core_v1  # or euai_core_v1
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- `http://127.0.0.1:8000/`

What you should see:

- both EU and DPDP rulepacks available in the dashboard scan configuration
- the configured `DEFAULT_RULEPACK_ID` preselected by default

You do not need separate backend runs for DPDP vs EUAI. Keep one backend running and switch the selected rulepack in the UI while configuring scans.

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

For repo development, prefer `--pack-id`. `--pack /path/to/*.yaml` is mainly for dev/testing custom packs.

## Client Bundle Command (`run_scan.py`)

If a client is using a generated/downloaded agent bundle (not this repo), the command is:

```bash
python run_scan.py --project-path /path/to/your/project --output-dir ./scan_results
```
e.g. 
```bash
python3 run_scan.py --project-path /Users/hardikgoel/PycharmProjects/CompliSense-AI/artefacts --output-dir ./scan_results
```

macOS/Linux full flow:

```bash
cd /path/to/complisense_agent
chmod +x setup_agent.sh
./setup_agent.sh
source complisense_env/bin/activate
python run_scan.py --project-path /path/to/your/project --output-dir ./scan_results
```

Windows full flow:

```bat
cd C:\path\to\complisense_agent
setup_agent.bat
complisense_env\Scripts\activate.bat
python run_scan.py --project-path "C:\path\to\your\project" --output-dir ".\scan_results"
```

If present, launcher wrappers can also be used:

- macOS/Linux: `./run_agent.sh --project-path /path/to/your/project --output-dir ./scan_results`
- Windows: `run_agent.bat --project-path "C:\path\to\your\project" --output-dir ".\scan_results"`

Outputs are written into the selected `--out` directory, especially:

- `compliance_findings.json`
- (compiled CLI path may also produce `findings.json` internally; `run_scan.py` normalizes output handling)
- `compliance_report.pdf` only when PDF output is enabled and source-mode bundle is used

If you see `Embedded rulepack not found for pack_id=...`, the bundle was generated from an older CLI build.
Run `make refresh-agent-bundles` and then regenerate/download the agent ZIP.

## Run The Desktop Agent UI

```bash
cd /Users/hardikgoel/PycharmProjects/CompliSense-AI
source 3.11_venv/bin/activate
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
MARKETING_SITE_URL=https://complisenseai.com
APP_BASE_URL=https://complisense-ai-backend.onrender.com
API_BASE_URL=https://api.complisenseai.com
COOKIE_DOMAIN=.complisenseai.com
SUPPORT_EMAIL=support@complisenseai.com
MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/complisense?retryWrites=true&w=majority
MONGO_DB=complisense
DEFAULT_RULEPACK_ID=dpdp_india_core_v1
JWT_SECRET=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ADMIN_API_TOKEN=replace-with-a-long-random-agent-token
CORS_ORIGINS=https://complisenseai.com,https://complisense-ai-backend.onrender.com,https://api.complisenseai.com
LOG_LEVEL=INFO
SECURE_COOKIES=true
```

If you use GitHub Actions, add these repository secrets with the same names:

- `MONGO_URI`
- `JWT_SECRET`
- `ADMIN_API_TOKEN`

`.github/workflows/backend-secrets-smoke.yml` maps those secrets into job environment variables and runs a backend health check. This covers GitHub Actions runs only. Render, Railway, or any other host still needs its own environment variables unless deployment is also performed through GitHub Actions.

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
