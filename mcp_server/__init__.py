"""ProjectLens MCP server — exposes the scan/compact/stats engine to any
MCP-compatible host (Cursor, VS Code Copilot Chat, Codex, Gemini CLI,
OpenCode, Trae, Kiro, Antigravity, ...).

This is a *separate distribution channel* from the Claude Code/Cowork
plugin. The plugin stays exactly as-is; this server is opt-in for users
whose tool of choice speaks MCP instead of the Claude plugin format.

Run as a stdio MCP server:

    python -m mcp_server

Wire into your tool's MCP config — see docs/integrations/ for per-tool
recipes.
"""
