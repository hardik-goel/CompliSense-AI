# CompliSense MCP Server

Exposes CompliSense's grounded, **read-only** compliance engine to MCP clients (e.g. Claude
Desktop) as tools. No database, no network, no credentials — the server runs standalone from
the repo. Everything is **readiness-framed, never a legal determination**.

## Tools

| Tool | Input | Returns |
|------|-------|---------|
| `list_rulepacks` | — | available rulepacks (DPDP India, EU AI Act) |
| `list_rules` | `pack_id` | rules with dual citations, enforcement dates, readiness framing |
| `get_questionnaire` | — | the Tier-0 readiness questionnaire |
| `score_readiness` | `answers`, `pack_id?` | applicability-gated DPDP readiness report (unknown = gap) |
| `infer_pii` | `field_names[]` | personal-data categories inferred from NAMES only |
| `infer_data_flows` | `sources[]` | PII-per-source map + cross-border flags (names only) |
| `list_connectors` | — | Tier-1 discovery connectors + required inputs |
| `connector_policy` | `provider` | read-only least-privilege policy for a connector |

`infer_pii` / `infer_data_flows` take field/column **names only** — never values.

## Run

```bash
pip install -r requirements.txt   # includes `mcp`
python -m mcp_server.server        # stdio MCP server
```

## Claude Desktop config

Add to `claude_desktop_config.json` (macOS:
`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "complisense": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/CompliSense-AI"
    }
  }
}
```

Use the repo's Python (or its virtualenv interpreter) so `compliance/`, `connectors/`, and
the rulepacks are importable.

## Design

- `mcp_server/tools.py` — pure tool registry + handlers (reuse `compliance.*` / `connectors`).
  DB-free and SDK-free, so it is unit-tested directly.
- `mcp_server/server.py` — MCP stdio transport; imports the `mcp` SDK lazily inside `main()`,
  so the package imports cleanly even without the SDK installed.
