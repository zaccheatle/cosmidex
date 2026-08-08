"""Shared MCPServer instance for the CosmiDex MCP server.

Lives in its own module, separate from both `mcp_server.py` (the entry point)
and the `tools/` modules, to avoid a circular import: each tool module needs
to import `mcp` from somewhere to use the `@mcp.tool()` decorator, and
`mcp_server.py` needs to import each tool module so its decorators actually
run and register the tool. If `mcp` were defined directly in `mcp_server.py`,
`mcp_server.py` would import a tool module, which would import `mcp` back out
of `mcp_server.py`, which is still in the middle of being imported —
a circular import. Defining `mcp` here instead means both `mcp_server.py` and
every module under `tools/` import it from this single, independent module,
so neither ever needs to import the other.
"""

from mcp.server import MCPServer

mcp = MCPServer("cosmidex")
