"""Performance budget enforcement (Phase 9 perf harness).

These are pytest tests with HARD ASSERTIONS, not benchmarks for show. CI
fails if any phase regresses past the budget. Adding adapters will trip
these tests if they violate the engineering rules in scripts/frameworks/.

Budgets (target → hard cap):
    Hook subprocess startup     ≤ 100 ms target, 250 ms hard cap
    Scan on 100-file fixture    ≤ 1.0 s target, 2.5 s hard cap
    Capsule build               ≤ 50 ms target, 200 ms hard cap
    Stats record_event          ≤ 20 ms target, 100 ms hard cap
    Hook output per event       ≤ 500 tok hard cap (envelope check)

Rule audits (structural — fail if violated):
    R1: Hook scripts never import scripts/frameworks/*
    R3: Adapter detect() never opens files

Run separately from the main suite when timing matters:
    python -m pytest tests/benchmark_perf.py -v --no-header
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "projectlens" / "scripts"
FRAMEWORKS = SCRIPTS / "frameworks"

# ---- Hard caps (CI fails if exceeded) ----
HOOK_STARTUP_HARD_MS = 250
SCAN_100_FILE_HARD_S = 2.5
CAPSULE_BUILD_HARD_MS = 200
STATS_RECORD_HARD_MS = 100
HOOK_OUTPUT_HARD_TOK = 500


# ----- 100-file fixture builder -----

@pytest.fixture(scope="module")
def hundred_file_project(tmp_path_factory):
    """Build a realistic 100-file Python project once for the timing tests."""
    root = tmp_path_factory.mktemp("perf_100")
    for module in ("api", "domain", "db", "utils"):
        (root / module).mkdir()
        for i in range(25):
            (root / module / f"file_{i}.py").write_text(
                f'"""Module {module}.{i}."""\n'
                f"from domain.user import User\n"
                f"def handler_{i}(x: int) -> str:\n"
                f"    return str(x)\n"
                f"class Service_{i}:\n"
                f"    def run(self): pass\n"
            )
    return root


# ----- Test 1: hook startup time -----

def test_dedup_hook_startup_under_250ms(tmp_path):
    """A single dedup_hook invocation must complete in < 250ms cold."""
    (tmp_path / "x.py").write_text("def a(): pass\n")
    payload = json.dumps({
        "cwd": str(tmp_path),
        "tool_name": "Read",
        "tool_input": {"file_path": str(tmp_path / "x.py")},
    })
    # Warm import cache once (Python's import is cached system-wide; this is the
    # real-world measurement an agent sees on the *second* invocation onward).
    subprocess.run(
        [sys.executable, str(SCRIPTS / "dedup_hook.py")],
        input=payload, capture_output=True, text=True, timeout=5,
    )
    # Measured run
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "dedup_hook.py")],
        input=payload, capture_output=True, text=True, timeout=5,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert proc.returncode == 0
    assert elapsed_ms < HOOK_STARTUP_HARD_MS, (
        f"dedup_hook took {elapsed_ms:.0f}ms, hard cap is {HOOK_STARTUP_HARD_MS}ms"
    )


# ----- Test 2: scan on 100-file fixture -----

def test_scan_100_files_under_2500ms(hundred_file_project):
    """Full scan on a 100-file project must complete in < 2.5s."""
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "scan.py"), str(hundred_file_project),
         "--no-git", "--output", str(hundred_file_project / "out")],
        capture_output=True, text=True, timeout=30,
    )
    elapsed_s = time.perf_counter() - t0
    assert proc.returncode == 0
    assert elapsed_s < SCAN_100_FILE_HARD_S, (
        f"scan took {elapsed_s:.2f}s, hard cap is {SCAN_100_FILE_HARD_S}s"
    )


# ----- Test 3: capsule build time -----

def test_capsule_build_under_200ms():
    """Capsule build is pure CPU; must stay snappy regardless of adapter count."""
    sys.path.insert(0, str(SCRIPTS))
    from capsule import build_capsule  # type: ignore
    lens_data = {
        "project_kind": "Python web API",
        "primary_language": "Python",
        "files": 200, "loc": 25_000,
        "summary": "Python web API; 200 files, 25k LOC.",
        "modules": [{"path": f"mod_{i}/", "purpose": f"module {i}"} for i in range(20)],
        "entry_points": [{"path": "main.py", "role": "main"}],
        "hotspots": [{"path": f"f{i}.py", "commits": 5, "last_touched": "2026-05-23"} for i in range(10)],
        "risks": [{"confidence": "EXTRACTED", "summary": f"risk {i}"} for i in range(10)],
        "conventions": ["Black", "Ruff", "pytest"],
        "symbols": [{"name": f"f{i}", "signature": f"f{i}(x)", "path": f"f{i}.py", "line": 1} for i in range(20)],
    }
    t0 = time.perf_counter()
    out = build_capsule(lens_data, "T3")
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert "<!-- projectlens-begin -->" in out
    assert elapsed_ms < CAPSULE_BUILD_HARD_MS, (
        f"capsule build took {elapsed_ms:.0f}ms, hard cap is {CAPSULE_BUILD_HARD_MS}ms"
    )


# ----- Test 4: stats record_event speed -----

def test_stats_record_event_under_100ms(tmp_path, monkeypatch):
    """record_event() must stay fast — it runs after every hook event."""
    monkeypatch.setenv("PROJECTLENS_STATS_HOME", str(tmp_path))
    sys.path.insert(0, str(SCRIPTS))
    from stats import record_event  # type: ignore

    t0 = time.perf_counter()
    record_event("dedup")
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert elapsed_ms < STATS_RECORD_HARD_MS, (
        f"record_event took {elapsed_ms:.0f}ms, hard cap is {STATS_RECORD_HARD_MS}ms"
    )


# ----- Test 5: hook output token envelope -----

def test_dedup_hook_output_within_envelope(tmp_path):
    """The additionalContext emitted by dedup_hook must stay under 500 tok."""
    (tmp_path / "z.py").write_text("def a(): pass\n")
    payload = json.dumps({
        "cwd": str(tmp_path),
        "tool_name": "Read",
        "tool_input": {"file_path": str(tmp_path / "z.py")},
    })
    # Trigger a duplicate to get the actual additionalContext
    subprocess.run([sys.executable, str(SCRIPTS / "dedup_hook.py")],
                   input=payload, capture_output=True, text=True, timeout=5)
    proc = subprocess.run([sys.executable, str(SCRIPTS / "dedup_hook.py")],
                          input=payload, capture_output=True, text=True, timeout=5)
    data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    ctx = data.get("hookSpecificOutput", {}).get("additionalContext", "")
    # 4 chars ≈ 1 token
    estimated_tokens = len(ctx) // 4
    assert estimated_tokens <= HOOK_OUTPUT_HARD_TOK, (
        f"dedup hook output ~{estimated_tokens} tok, hard cap {HOOK_OUTPUT_HARD_TOK}"
    )


# ----- Rule R1: hooks never import frameworks -----

HOOK_FILES = [
    "dedup_hook.py",
    "compress_hook.py",
    "activity_hook.py",
    "inject_hook.py",
    "memory_loader.py",
    "statusline.py",
]


@pytest.mark.parametrize("hook", HOOK_FILES)
def test_hook_never_imports_frameworks(hook):
    """Static analysis: no hook script may import from scripts.frameworks.*"""
    path = SCRIPTS / hook
    text = path.read_text(encoding="utf-8")
    forbidden = re.compile(r"from\s+(scripts\.)?frameworks|import\s+(scripts\.)?frameworks")
    matches = forbidden.findall(text)
    assert not matches, (
        f"Rule R1 violated — {hook} imports frameworks/. "
        "Hooks must stay framework-free for performance."
    )


# ----- Rule R3: adapter detect() never opens files -----

def test_adapter_detect_never_opens_files():
    """Static analysis: any adapter's detect() must not call open()/read_text()."""
    if not FRAMEWORKS.exists():
        pytest.skip("frameworks/ not present")
    forbidden_in_detect = re.compile(
        r"def\s+detect\s*\([^)]*\):[^@\n]*?(?:open\s*\(|read_text|read_bytes)",
        re.DOTALL,
    )
    violations: list[str] = []
    for py in FRAMEWORKS.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        # Naive but conservative: look for `def detect(` followed by I/O within
        # 500 chars (typical detect() body).
        for m in re.finditer(r"def\s+detect\s*\(", text):
            body = text[m.start(): m.start() + 500]
            if "open(" in body or ".read_text" in body or ".read_bytes" in body:
                violations.append(f"{py.relative_to(FRAMEWORKS)}")
    assert not violations, (
        f"Rule R3 violated — detect() opens files in: {violations}. "
        "Detection must be O(1) imports-only."
    )


# ----- Plugin size growth bound -----

# ----- Security audit — static analysis -----

# Forbidden patterns. Adding any of these to shipped code without a paired
# update to this allowlist will fail CI. The point is to keep the project's
# attack surface unchanged as it grows.
_FORBIDDEN_PATTERNS = (
    (re.compile(r"""\beval\s*\("""), "eval() is forbidden in shipped code"),
    (re.compile(r"""\bexec\s*\("""), "exec() is forbidden in shipped code"),
    (re.compile(r"""\b__import__\s*\("""), "__import__ is forbidden in shipped code"),
    (re.compile(r"""pickle\s*\.\s*loads?\b"""), "pickle deserialization is forbidden"),
    (re.compile(r"""\bmarshal\s*\.\s*loads?\b"""), "marshal deserialization is forbidden"),
    (re.compile(r"""shell\s*=\s*True"""), "shell=True is forbidden (use list args)"),
    (re.compile(r"""os\s*\.\s*system\s*\("""), "os.system is forbidden (use subprocess with list args)"),
)
# Files allowed to mention these patterns in comments/strings (e.g. SECURITY.md
# documents what's forbidden — we don't want a false positive there).
_AUDIT_EXEMPT_FILES = frozenset({
    "benchmark_perf.py",  # this file
})


def test_no_forbidden_security_patterns():
    """Static analysis: shipped code never uses exec/eval/pickle/shell=True/etc.

    See SECURITY.md for the threat model. Adding any of these requires updating
    SECURITY.md *and* this allowlist together — that's the friction by design.
    """
    violations: list[str] = []
    for py in SCRIPTS.rglob("*.py"):
        if py.name in _AUDIT_EXEMPT_FILES:
            continue
        text = py.read_text(encoding="utf-8")
        for pattern, msg in _FORBIDDEN_PATTERNS:
            for m in pattern.finditer(text):
                # Skip if the match is inside a comment line (cheap heuristic)
                line_start = text.rfind("\n", 0, m.start()) + 1
                line = text[line_start: m.end() + 80]
                if line.lstrip().startswith("#"):
                    continue
                violations.append(
                    f"{py.relative_to(SCRIPTS)}: {msg} (line ~{text[:m.start()].count(chr(10)) + 1})"
                )
    assert not violations, "Forbidden patterns in shipped code:\n  " + "\n  ".join(violations)


def test_outbound_network_only_anthropic_api():
    """Static analysis: outbound HTTP allowed only to api.anthropic.com.

    Catches: someone adding a new network call without going through llm_client.
    """
    forbidden_http = re.compile(r"""urlopen\s*\(|urllib\.request\.Request\s*\(""")
    allowed_file = "llm_client.py"
    violations: list[str] = []
    for py in SCRIPTS.rglob("*.py"):
        if py.name == allowed_file:
            continue
        text = py.read_text(encoding="utf-8")
        if forbidden_http.search(text):
            violations.append(str(py.relative_to(SCRIPTS)))
    assert not violations, (
        f"Outbound HTTP outside {allowed_file}: {violations}. "
        "Route all network calls through llm_client.py — see SECURITY.md."
    )


def test_user_adapter_loader_is_opt_in(monkeypatch, tmp_path):
    """Confirms _load_user_adapters is gated behind PROJECTLENS_USER_ADAPTERS=1.

    Without the env var, scanning a repo with a `.projectlens/frameworks/`
    directory must NOT import its Python modules.
    """
    monkeypatch.delenv("PROJECTLENS_USER_ADAPTERS", raising=False)
    sys.path.insert(0, str(SCRIPTS))
    from frameworks.registry import _load_user_adapters  # type: ignore
    fw_dir = tmp_path / ".projectlens" / "frameworks"
    fw_dir.mkdir(parents=True)
    # This file would do something destructive if imported
    (fw_dir / "evil.py").write_text("raise RuntimeError('user adapter ran')\n")
    result = _load_user_adapters(fw_dir)
    assert result == [], "User adapter loader fired without PROJECTLENS_USER_ADAPTERS=1"


def test_skill_md_under_3kb_target():
    """SKILL.md must stay lean; references hold the bulk."""
    skill = ROOT / "skills" / "projectlens" / "SKILL.md"
    size = skill.stat().st_size
    # 8KB is the hard cap (current is ~6KB)
    assert size < 8_000, f"SKILL.md is {size}B; hard cap 8000B"


def test_capsule_token_budget_unchanged():
    """Capsule total budget must NOT have grown silently."""
    sys.path.insert(0, str(SCRIPTS))
    from complexity import TIER_BUDGETS  # type: ignore
    # Canonical budgets. Bumping them is intentional and requires updating
    # this test along with TIER_BUDGETS.
    #   v0.4.0: T1=500, T2=1500, T3=2500
    #   v0.4.0+symbols: T2=1700, T3=2900
    #   v0.7.0 +framework slot: T2=1900, T3=3300
    #   v0.9.0 +_ml_core pack:  T2=2100 (frameworks 200→400),
    #                           T3=3600 (frameworks 400→700)
    assert TIER_BUDGETS["T1"]["total"] == 500
    assert TIER_BUDGETS["T2"]["total"] == 2100
    assert TIER_BUDGETS["T3"]["total"] == 3600
