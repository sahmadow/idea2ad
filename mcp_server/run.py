"""
MCP Server entrypoint — Streamable HTTP transport.

Usage:
    python -m mcp_server.run
    MCP_PORT=9000 python -m mcp_server.run
"""

import os
import sys

# Add project root to path so `app.*` imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    port = int(os.environ.get("MCP_PORT", "8100"))
    host = os.environ.get("MCP_HOST", "0.0.0.0")

    from mcp_server.server import mcp

    mcp.settings.host = host
    mcp.settings.port = port

    print(f"Starting LaunchAd MCP server on {host}:{port}")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
