"""Tests for the UserPromptSubmit injection hook (Phase 3)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "skills" / "lensify" / "scripts" / "inject_hook.py"
)

SAMPLE_SECTIONS = {
    "version": 1,
    "tier": "T2",
    "project_name": "demo",
    "primary_language": "Python",
    "module_paths": ["api", "domain", "db"],
    "entry_paths": ["main.py"],
    "sections": {
        "summary": "# SUMMARY\n\nDemo project in Python.",
        "entry": "## ENTRY\n- `main.py` — main",
        "modules": "## MODULES\n\n- api/: HTTP routes\n- domain/: business logic",
        "conventions": "## CONVENTIONS\n- Black + Ruff",
        "hotspots": "## HOTSPOTS\n- api/auth.py — 12 commits",
        "risks": "## RISKS\n- [EXTRACTED] cyclical imports",
    },
}


def run_hook(payload: dict, env_extra: dict | None = None) -> dict:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    if not proc.stdout.strip():
        return {}
    return json.loads(proc.stdout)


@pytest.fixture
def project_with_sections(tmp_path) -> Path:
    out = tmp_path / "lensify-out"
    out.mkdir()
    (out / "lens.sections.json").write_text(json.dumps(SAMPLE_SECTIONS))
    return tmp_path


def test_hook_silent_without_sections_file(tmp_path):
    out = run_hook({"cwd": str(tmp_path), "prompt": "what does this do?"})
    assert "hookSpecificOutput" not in out


def test_hook_silent_on_empty_prompt(project_with_sections):
    out = run_hook({"cwd": str(project_with_sections), "prompt": ""})
    assert "hookSpecificOutput" not in out


def test_hook_injects_summary_for_summary_prompt(project_with_sections):
    out = run_hook({"cwd": str(project_with_sections), "prompt": "what is this project?"})
    assert "hookSpecificOutput" in out
    text = out["hookSpecificOutput"]["additionalContext"]
    assert "SUMMARY" in text
    assert "Demo project" in text


def test_hook_injects_modules_when_module_named(project_with_sections):
    out = run_hook({
        "cwd": str(project_with_sections),
        "prompt": "where is the auth thing — in api?",
    })
    assert "hookSpecificOutput" in out
    text = out["hookSpecificOutput"]["additionalContext"]
    assert "MODULES" in text


def test_hook_appends_session_when_session_intent(tmp_path):
    out_dir = tmp_path / "lensify-out"
    out_dir.mkdir()
    (out_dir / "lens.sections.json").write_text(json.dumps(SAMPLE_SECTIONS))
    # Provide a session capsule on disk too
    (out_dir / "SESSION.capsule.md").write_text(
        "<!-- lensify-session-begin -->\n"
        "# SESSION ACTIVITY\n\nTurn 5 · 3 files seen.\n"
        "<!-- lensify-session-end -->\n"
    )
    out = run_hook({
        "cwd": str(tmp_path),
        "prompt": "what have we done so far in this session?",
    })
    assert "hookSpecificOutput" in out
    text = out["hookSpecificOutput"]["additionalContext"]
    assert "SESSION ACTIVITY" in text


def test_hook_handles_malformed_sections_json(tmp_path):
    out_dir = tmp_path / "lensify-out"
    out_dir.mkdir()
    (out_dir / "lens.sections.json").write_text("not valid json {{")
    out = run_hook({"cwd": str(tmp_path), "prompt": "what is this project?"})
    assert "hookSpecificOutput" not in out


def test_hook_disabled_by_env(project_with_sections):
    out = run_hook(
        {"cwd": str(project_with_sections), "prompt": "what is this?"},
        env_extra={"LENSIFY_DEDUP": "0"},
    )
    assert "hookSpecificOutput" not in out


def test_hook_caps_section_count(project_with_sections):
    """A prompt that triggers many sections should still cap at MAX_SECTIONS."""
    out = run_hook({
        "cwd": str(project_with_sections),
        "prompt": "what is this — how do I run it where does code live what's the style hot risks",
    })
    assert "hookSpecificOutput" in out
    text = out["hookSpecificOutput"]["additionalContext"]
    # Count "## " headers — should be at most MAX_SECTIONS = 4
    sec_count = text.count("\n## ") + text.count("\n# ")
    assert sec_count <= 5  # allow a little slack for the wrapper header line


def test_hook_handles_empty_stdin():
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input="",
        capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0


def test_hook_handles_malformed_stdin():
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input="not json",
        capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0
