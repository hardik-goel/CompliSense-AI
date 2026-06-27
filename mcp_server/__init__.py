"""CompliSense MCP server (Phase 6).

Exposes CompliSense's grounded, read-only compliance engine to MCP clients (e.g. Claude
Desktop) as tools: list rulepacks/rules with citations, score Tier-0 readiness, infer PII
and data flows from field names, and fetch per-connector least-privilege policies.

The tool LOGIC (mcp_server/tools.py) is pure and DB-free, so the server runs standalone
without the SaaS backend or Mongo. The MCP transport (mcp_server/server.py) imports the
`mcp` SDK lazily, so this package imports cleanly even where `mcp` isn't installed.

Everything here is read-only and readiness-framed — never a legal determination.
"""

from mcp_server.tools import TOOLS, call_tool, list_tools

__all__ = ["TOOLS", "call_tool", "list_tools"]
