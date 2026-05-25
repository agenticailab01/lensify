"""Entry point for `python -m mcp_server` — runs the stdio MCP server loop."""
from .server import serve_stdio

if __name__ == "__main__":
    serve_stdio()
