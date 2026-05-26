"""Lensify MCP server (pure stdlib).

Implements the Model Context Protocol over JSON-RPC 2.0 stdio. Exposes
three tools:

    lensify_scan      — one-shot lens + capsule for a project
    lensify_compact   — generate WORKING_CONTEXT.md from session state
    lensify_stats     — lifetime savings report

Why pure stdlib (no `mcp` SDK dependency):

  • Users installing this package shouldn't need a transitive web of deps.
  • The MCP stdio protocol is JSON-RPC 2.0 — well-specified, easy to do
    by hand.
  • We control the supported subset and can extend predictably.
  • Less code surface for security audit (see SECURITY.md).

Protocol scope implemented:
  - initialize
  - initialized (notification, ignored)
  - tools/list
  - tools/call
  - ping
  - shutdown (notification)

That's enough for Cursor, VS Code Copilot Chat, Codex, Gemini CLI, and
most other MCP hosts to discover and call our tools.

If a host requests a method we don't implement, we return a JSON-RPC
error -32601 (Method not found) — never crashes.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import traceback
from pathlib import Path
from typing import Any

# Add the scripts/ directory to sys.path so we can import the engine.
# This keeps the MCP server independent of how the package was installed —
# works whether via PyPI, a git clone, or running from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO_ROOT / "skills" / "lensify" / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


# ---- Tool implementations — thin wrappers over the engine ----

def _tool_scan(args: dict) -> dict:
    """Wrapper for scripts/scan.py::scan()."""
    from scan import scan as engine_scan  # type: ignore
    path = args.get("path")
    if not path:
        raise ValueError("'path' is required")
    tier = args.get("tier", "auto")
    override = None if tier in ("auto", None) else tier
    if override and override not in ("T1", "T2", "T3"):
        raise ValueError(f"invalid tier: {tier!r}")
    engine_scan(
        str(path),
        tier_override=override,
        capsule_only=bool(args.get("capsule_only", False)),
        ast_only=bool(args.get("ast_only", False)),
        no_git=bool(args.get("no_git", False)),
        output_dir=args.get("output_dir"),
    )
    out_dir = (Path(args["output_dir"])
               if args.get("output_dir")
               else Path(path) / "lensify-out")
    capsule = out_dir / "LENS.capsule.md"
    lens_json = out_dir / "lens.json"
    payload = {
        "capsule_path": str(capsule) if capsule.exists() else None,
        "lens_html_path": str(out_dir / "LENS.html") if (out_dir / "LENS.html").exists() else None,
    }
    if lens_json.exists():
        try:
            payload["summary"] = json.loads(lens_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    if capsule.exists():
        payload["capsule"] = capsule.read_text(encoding="utf-8")
    return payload


def _tool_compact(args: dict) -> dict:
    """Wrapper for scripts/compact.py::run_compact()."""
    from compact import run_compact  # type: ignore
    project = args.get("path") or args.get("session_dir") or "."
    meta = run_compact(
        project,
        use_llm=bool(args.get("llm", False)),
        output_dir=args.get("output_dir"),
    )
    # Attach the body for convenience (the host may want to inject it)
    out_path = Path(meta.get("path", ""))
    if out_path.exists():
        try:
            meta["body"] = out_path.read_text(encoding="utf-8")
        except OSError:
            pass
    return meta


def _tool_stats(args: dict) -> dict:
    """Wrapper for scripts/stats.py — returns the lifetime stats dict."""
    from stats import load_stats  # type: ignore
    return load_stats().to_dict()


TOOLS: dict[str, dict] = {
    "lensify_scan": {
        "description": "Generate a one-page project lens + token-optimized "
                       "context capsule. Returns the capsule text plus paths "
                       "to LENS.html and LENS.capsule.md. Auto-detects tier "
                       "(T1/T2/T3) unless overridden.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project root path"},
                "tier": {"type": "string", "enum": ["auto", "T1", "T2", "T3"]},
                "capsule_only": {"type": "boolean"},
                "ast_only": {"type": "boolean"},
                "no_git": {"type": "boolean"},
                "output_dir": {"type": "string"},
            },
            "required": ["path"],
        },
        "handler": _tool_scan,
    },
    "lensify_compact": {
        "description": "Generate WORKING_CONTEXT.md from the current session's "
                       "tracked activity. Used mid-session to reclaim 8-25k "
                       "tokens by /clear-with-continuity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project root"},
                "llm": {"type": "boolean", "description": "Use Haiku for enhanced summary"},
                "output_dir": {"type": "string"},
            },
            "required": ["path"],
        },
        "handler": _tool_compact,
    },
    "lensify_stats": {
        "description": "Lifetime Lensify stats: scans run, tokens saved, "
                       "dedup hits, edits tracked, compaction reclaim totals.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": _tool_stats,
    },
}


# ---- JSON-RPC 2.0 protocol ----

PROTOCOL_VERSION = "2024-11-05"  # MCP spec version we target
SERVER_INFO = {"name": "lensify-mcp", "version": "0.15.0"}


def _ok(rid: Any, result: Any) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": rid, "result": result})


def _err(rid: Any, code: int, message: str, data: Any = None) -> str:
    obj = {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}
    if data is not None:
        obj["error"]["data"] = data
    return json.dumps(obj)


def _handle_request(req: dict) -> str | None:
    """Returns the JSON-RPC response string, or None for notifications."""
    method = req.get("method", "")
    rid = req.get("id")
    is_notification = rid is None
    params = req.get("params", {}) or {}

    # Routing
    if method == "initialize":
        return _ok(rid, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
        })

    if method == "initialized" or method == "notifications/initialized":
        return None  # notification, no reply

    if method == "ping":
        return _ok(rid, {})

    if method == "tools/list":
        tools_out = []
        for name, spec in TOOLS.items():
            tools_out.append({
                "name": name,
                "description": spec["description"],
                "inputSchema": spec["inputSchema"],
            })
        return _ok(rid, {"tools": tools_out})

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {}) or {}
        spec = TOOLS.get(tool_name)
        if spec is None:
            return _err(rid, -32602, f"Unknown tool: {tool_name!r}")
        # CRITICAL: MCP stdio uses stdout for JSON-RPC. Tool handlers (scan.py
        # prints a banner, compact.py logs progress) must not bleed into the
        # protocol stream. Capture stdout during execution and discard.
        # Stderr is left alone — host logs can show diagnostic info if needed.
        captured = io.StringIO()
        try:
            with contextlib.redirect_stdout(captured):
                result = spec["handler"](tool_args)
        except ValueError as e:
            return _err(rid, -32602, f"Invalid params: {e}")
        except Exception as e:  # noqa: BLE001
            return _err(rid, -32603, f"Tool error: {e}",
                        data=traceback.format_exc()[:2000])
        # Per MCP spec, tools/call returns {content: [TextContent...]}
        return _ok(rid, {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "isError": False,
        })

    if method == "shutdown":
        return _ok(rid, {})

    # Notifications we don't care about → silent ignore
    if is_notification:
        return None

    return _err(rid, -32601, f"Method not found: {method}")


def serve_stdio() -> None:
    """Read JSON-RPC messages from stdin, write replies to stdout.

    MCP uses newline-delimited JSON over stdio. We loop forever; the host
    disconnects by closing stdin, which raises EOFError → clean exit.

    Errors here never propagate to the host as exceptions — they get
    serialised as JSON-RPC errors. The MCP host should always see a
    well-formed response or no response (for notifications).
    """
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            # Can't recover an id; emit a parse error with id=null
            sys.stdout.write(_err(None, -32700, "Parse error") + "\n")
            sys.stdout.flush()
            continue
        try:
            response = _handle_request(req)
        except Exception as e:  # noqa: BLE001
            response = _err(req.get("id"), -32603, f"Internal error: {e}")
        if response is not None:
            sys.stdout.write(response + "\n")
            sys.stdout.flush()
