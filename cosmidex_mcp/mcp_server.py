"""Entry point for the CosmiDex MCP server.

Imports the shared `mcp` instance and each `tools/` module — the tool-module
imports exist for their side effect (running the `@mcp.tool()` decorators
inside them to register their tools), not to use any name imported from them
directly. Running this file starts the server.
"""

from cosmidex_mcp.mcp_instance import mcp
from cosmidex_mcp.tools.exoplanets import get_planet

if __name__ == "__main__":
    mcp.run()
