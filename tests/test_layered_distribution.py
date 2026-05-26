"""Tests for the three non-plugin distribution channels:

  • CLI entry point             (scan.py main)
  • --install-agents-md flag    (scan.py + capsule.install_into)
  • MCP server                  (mcp_server stdio JSON-RPC roundtrip)

These tests guarantee the layered architecture stays functional. They are
independent of the plugin tests so the plugin can change without breaking
the CLI/MCP/AGENTS.md surface (and vice versa).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "skills" / "lensify" / "scripts"


# ---- CLI entry point ----

@pytest.fixture
def tiny_project(tmp_path):
    (tmp_path / "main.py").write_text("def main(): return 42\n")
    (tmp_path / "utils.py").write_text("def helper(): pass\n")
    return tmp_path


def test_cli_runs_and_writes_capsule(tiny_project):
    """`python scan.py <path>` produces LENS.capsule.md."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "scan.py"), str(tiny_project),
         "--no-git", "--output", str(tiny_project / "out")],
        capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    assert (tiny_project / "out" / "LENS.capsule.md").exists()


def test_cli_version_flag():
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "scan.py"), "--version"],
        capture_output=True, text=True, timeout=5,
    )
    assert proc.returncode == 0
    assert "lensify" in proc.stdout
    # Version should start with a digit
    assert any(c.isdigit() for c in proc.stdout)


# ---- AGENTS.md install mode ----

def test_install_agents_md_writes_capsule(tiny_project):
    agents = tiny_project / "AGENTS.md"
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "scan.py"), str(tiny_project),
         "--no-git", "--install-agents-md"],
        capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    assert agents.exists()
    text = agents.read_text(encoding="utf-8")
    assert "<!-- lensify-begin -->" in text
    assert "<!-- lensify-end -->" in text


def test_install_agents_md_is_idempotent(tiny_project):
    """Second invocation replaces only the marked block, preserves the rest."""
    agents = tiny_project / "AGENTS.md"
    agents.write_text(
        "# My project\n\n"
        "Custom instructions for the agent.\n\n"
        "Do not run tests in production.\n"
    )
    # Run once
    subprocess.run(
        [sys.executable, str(SCRIPTS / "scan.py"), str(tiny_project),
         "--no-git", "--install-agents-md"],
        capture_output=True, text=True, timeout=15, check=True,
    )
    first = agents.read_text(encoding="utf-8")
    assert "Do not run tests in production" in first
    assert "<!-- lensify-begin -->" in first
    # Run again
    subprocess.run(
        [sys.executable, str(SCRIPTS / "scan.py"), str(tiny_project),
         "--no-git", "--install-agents-md"],
        capture_output=True, text=True, timeout=15, check=True,
    )
    second = agents.read_text(encoding="utf-8")
    # Custom content still there
    assert "Do not run tests in production" in second
    # Only one capsule block (idempotent — not duplicated)
    assert second.count("<!-- lensify-begin -->") == 1


def test_install_agents_md_custom_path(tiny_project):
    """Custom filename works (e.g. GEMINI.md, CLAUDE.md)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "scan.py"), str(tiny_project),
         "--no-git", "--install-agents-md", "GEMINI.md"],
        capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    gemini = tiny_project / "GEMINI.md"
    assert gemini.exists()
    assert "<!-- lensify-begin -->" in gemini.read_text(encoding="utf-8")


# ---- MCP server (stdio JSON-RPC) ----

def _send_mcp(*messages: dict, timeout: int = 10) -> list[dict]:
    """Spawn the MCP server, send messages, return parsed responses."""
    payload = "\n".join(json.dumps(m) for m in messages) + "\n"
    env_path = f"{REPO_ROOT}:{SCRIPTS}"
    proc = subprocess.run(
        [sys.executable, "-m", "mcp_server"],
        input=payload, capture_output=True, text=True, timeout=timeout,
        cwd=str(REPO_ROOT),
        env={"PYTHONPATH": env_path, "PATH": ""},
    )
    out: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def test_mcp_initialize():
    responses = _send_mcp(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )
    assert len(responses) == 1
    r = responses[0]
    assert r["id"] == 1
    assert "result" in r
    assert "serverInfo" in r["result"]
    assert r["result"]["serverInfo"]["name"] == "lensify-mcp"


def test_mcp_tools_list():
    responses = _send_mcp(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    )
    r = responses[0]
    assert "result" in r
    names = {t["name"] for t in r["result"]["tools"]}
    assert names == {"lensify_scan", "lensify_compact", "lensify_stats"}


def test_mcp_call_scan(tiny_project):
    responses = _send_mcp(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "lensify_scan",
            "arguments": {"path": str(tiny_project), "no_git": True},
        }},
        timeout=20,
    )
    r = responses[0]
    assert "result" in r, f"MCP error: {r}"
    payload = json.loads(r["result"]["content"][0]["text"])
    assert "capsule" in payload
    assert "SUMMARY" in payload["capsule"]


def test_mcp_unknown_method_returns_error():
    responses = _send_mcp(
        {"jsonrpc": "2.0", "id": 1, "method": "no_such_method", "params": {}},
    )
    r = responses[0]
    assert "error" in r
    assert r["error"]["code"] == -32601


def test_mcp_ignores_notifications():
    """Initialization notification has no id — server must not reply."""
    responses = _send_mcp(
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}},
    )
    # Only the ping should have a reply
    assert len(responses) == 1
    assert responses[0]["id"] == 1


def test_mcp_malformed_request_does_not_crash():
    """Server tolerates bad JSON and continues processing."""
    payload = "not valid json\n" + json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}
    }) + "\n"
    env_path = f"{REPO_ROOT}:{SCRIPTS}"
    proc = subprocess.run(
        [sys.executable, "-m", "mcp_server"],
        input=payload, capture_output=True, text=True, timeout=10,
        cwd=str(REPO_ROOT),
        env={"PYTHONPATH": env_path, "PATH": ""},
    )
    assert proc.returncode == 0
    # Should produce a parse-error reply AND the ping reply
    lines = [l for l in proc.stdout.splitlines() if l.strip()]
    assert len(lines) >= 2
