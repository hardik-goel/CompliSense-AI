"""CompliSense MCP stdio server (Phase 6.2).

Wraps the pure tool registry (mcp_server/tools.py) in a Model Context Protocol server over
stdio, so MCP clients (e.g. Claude Desktop) can call CompliSense's grounded, read-only
compliance tools. Run with:

    python -m mcp_server.server

The `mcp` SDK is imported lazily inside ``main`` so this module imports cleanly even where
the SDK isn't installed (the tool registry + tests never need it).
"""

from __future__ import annotations

import json

SERVER_NAME = "complisense"


def _serialize(result) -> str:
    return json.dumps(result, default=str, ensure_ascii=False)


async def main() -> None:
    try:
        import mcp.types as types
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "The 'mcp' package is required to run the MCP server. Install it: pip install mcp"
        ) from exc

    from mcp_server.tools import call_tool, list_tools

    server = Server(SERVER_NAME)

    @server.list_tools()
    async def handle_list_tools():
        return [
            types.Tool(name=t["name"], description=t["description"], inputSchema=t["inputSchema"])
            for t in list_tools()
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict | None):
        try:
            result = call_tool(name, arguments or {})
            return [types.TextContent(type="text", text=_serialize(result))]
        except (KeyError, ValueError) as exc:
            return [types.TextContent(type="text", text=_serialize({"error": str(exc)}))]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run() -> None:  # pragma: no cover - thin entrypoint
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":  # pragma: no cover
    run()
