"""Tests for the framework adapter registry + base class contract."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

# Make sure the frameworks package is importable
import sys
SCRIPTS = Path(__file__).resolve().parent.parent / "plugins" / "lensify" / "skills" / "lensify"
sys.path.insert(0, str(SCRIPTS))

from scripts.frameworks.base import (  # noqa: E402
    FrameworkAdapter, FrameworkInfo, FrameworkEntry,
    PRIORITY_HIGH, PRIORITY_MEDIUM, ABSOLUTE_MAX_ENTRIES, cap_entries,
)
from scripts.frameworks.registry import (  # noqa: E402
    load_manifest, _collect_imports, match_manifest_to_imports,
    discover_adapter_classes, run_adapters, ManifestEntry,
)
from scripts.walker import walk  # noqa: E402
from scripts.ast_parser import parse_all  # noqa: E402


# ----- Base class validation -----

class _GoodAdapter(FrameworkAdapter):
    name = "good"
    detect_signatures = ("import good",)
    priority = PRIORITY_MEDIUM
    max_entries = 10

    def extract(self, walk_result, parsed_files):
        return FrameworkInfo(name=self.name)


def test_good_adapter_validates():
    assert _GoodAdapter.validate_class() == []


def test_unnamed_adapter_fails_validation():
    class Bad(FrameworkAdapter):
        detect_signatures = ("x",)

        def extract(self, walk_result, parsed_files):
            return FrameworkInfo(name="x")

    errs = Bad.validate_class()
    assert any("name" in e for e in errs)


def test_signatureless_adapter_fails_validation():
    class Bad(FrameworkAdapter):
        name = "x"

        def extract(self, walk_result, parsed_files):
            return FrameworkInfo(name="x")

    errs = Bad.validate_class()
    assert any("detect_signatures" in e for e in errs)


def test_oversized_max_entries_fails():
    class Bad(FrameworkAdapter):
        name = "x"
        detect_signatures = ("x",)
        max_entries = ABSOLUTE_MAX_ENTRIES + 1

        def extract(self, walk_result, parsed_files):
            return FrameworkInfo(name="x")

    errs = Bad.validate_class()
    assert any("max_entries" in e for e in errs)


def test_priority_out_of_range_fails():
    class Bad(FrameworkAdapter):
        name = "x"
        detect_signatures = ("x",)
        priority = 500

        def extract(self, walk_result, parsed_files):
            return FrameworkInfo(name="x")

    errs = Bad.validate_class()
    assert any("priority" in e for e in errs)


# ----- Default detect() logic -----

def test_default_detect_matches_import(tmp_path):
    (tmp_path / "a.py").write_text("import good\n")
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    assert _GoodAdapter.detect(walk_result, parsed) is True


def test_default_detect_no_match(tmp_path):
    (tmp_path / "a.py").write_text("import unrelated\n")
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    assert _GoodAdapter.detect(walk_result, parsed) is False


# ----- Manifest loading -----

def test_manifest_loads_default():
    manifest = load_manifest()
    # Built-in manifest has at least the fastapi entry
    names = {entry.name for entry in manifest}
    assert "fastapi" in names


def test_manifest_handles_missing_file(tmp_path):
    assert load_manifest(tmp_path / "missing.json") == []


def test_manifest_handles_corrupted(tmp_path):
    p = tmp_path / "m.json"
    p.write_text("not json {{")
    assert load_manifest(p) == []


def test_manifest_handles_non_dict(tmp_path):
    p = tmp_path / "m.json"
    p.write_text("[1, 2, 3]")
    assert load_manifest(p) == []


# ----- Import collection + signature matching -----

def test_collect_imports_lowercases(tmp_path):
    (tmp_path / "x.py").write_text("import FOO\nimport bar\nfrom baz import x\n")
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    imports = _collect_imports(parsed)
    assert "foo" in imports
    assert "bar" in imports
    assert "baz" in imports


def test_match_manifest_to_imports():
    manifest = [
        ManifestEntry("fastapi", "_enterprise.fastapi", ["import fastapi"]),
        ManifestEntry("unrelated", "_enterprise.never", ["import never"]),
    ]
    matched = match_manifest_to_imports(manifest, {"fastapi", "os", "sys"})
    names = [m.name for m in matched]
    assert names == ["fastapi"]


# ----- Discovery only loads matched modules -----

def test_discover_skips_unmatched_modules(tmp_path):
    (tmp_path / "a.py").write_text("import os\n")
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    classes = discover_adapter_classes(parsed)
    # No FastAPI imports present → no FastAPI adapter loaded
    names = [c.name for c in classes]
    assert "fastapi" not in names


def test_discover_loads_matched_modules(tmp_path):
    (tmp_path / "a.py").write_text("import fastapi\nfrom fastapi import APIRouter\n")
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    classes = discover_adapter_classes(parsed)
    names = [c.name for c in classes]
    assert "fastapi" in names


# ----- run_adapters end-to-end -----

def test_run_adapters_returns_priority_sorted(tmp_path):
    (tmp_path / "main.py").write_text(
        "import fastapi\n"
        "app = fastapi.FastAPI()\n"
        '@app.get("/users")\n'
        "def list_users(): pass\n"
    )
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    infos = run_adapters(walk_result, parsed, project_root=tmp_path)
    assert infos  # at least one detected
    fastapi_info = next((i for i in infos if i.name == "fastapi"), None)
    assert fastapi_info is not None
    assert any(e.kind == "route" for e in fastapi_info.entries)


def test_run_adapters_empty_project(tmp_path):
    infos = run_adapters(walk_result_for(tmp_path), [], project_root=tmp_path)
    assert infos == []


def walk_result_for(path):
    return walk(str(path))


def test_run_adapters_enforces_max_entries(tmp_path):
    # Create a file with > max_entries routes
    body = "import fastapi\napp = fastapi.FastAPI()\n"
    for i in range(50):  # max_entries is 25
        body += f'@app.get("/r{i}")\ndef h_{i}(): pass\n'
    (tmp_path / "many.py").write_text(body)
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    infos = run_adapters(walk_result, parsed, project_root=tmp_path)
    fastapi_info = next(i for i in infos if i.name == "fastapi")
    assert len(fastapi_info.entries) <= 25


# ----- User adapter slot -----

USER_ADAPTER_SOURCE = """
from scripts.frameworks.base import FrameworkAdapter, FrameworkInfo, FrameworkEntry

class CustomAdapter(FrameworkAdapter):
    name = "custom_thing"
    detect_signatures = ("import some_lib",)
    priority = 30
    max_entries = 5

    def extract(self, walk_result, parsed_files):
        return FrameworkInfo(
            name=self.name,
            entries=[FrameworkEntry(kind="thing", name="hello", path="x", line=1)],
        )
"""


def test_user_adapter_loaded_from_project_dir(tmp_path, monkeypatch):
    # User-adapter loading is opt-in for security (running arbitrary
    # Python from scanned repos). Power users set LENSIFY_USER_ADAPTERS=1.
    monkeypatch.setenv("LENSIFY_USER_ADAPTERS", "1")
    (tmp_path / "a.py").write_text("import some_lib\n")
    fw_dir = tmp_path / ".lensify" / "frameworks"
    fw_dir.mkdir(parents=True)
    (fw_dir / "custom.py").write_text(USER_ADAPTER_SOURCE)

    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    classes = discover_adapter_classes(parsed, user_dir=fw_dir)
    names = [c.name for c in classes]
    assert "custom_thing" in names


def test_user_adapters_disabled_by_default(tmp_path, monkeypatch):
    """Without LENSIFY_USER_ADAPTERS=1, the user-adapter dir is ignored."""
    monkeypatch.delenv("LENSIFY_USER_ADAPTERS", raising=False)
    (tmp_path / "a.py").write_text("import some_lib\n")
    fw_dir = tmp_path / ".lensify" / "frameworks"
    fw_dir.mkdir(parents=True)
    (fw_dir / "custom.py").write_text(USER_ADAPTER_SOURCE)

    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    classes = discover_adapter_classes(parsed, user_dir=fw_dir)
    names = [c.name for c in classes]
    assert "custom_thing" not in names


def test_malformed_user_adapter_silently_ignored(tmp_path, monkeypatch):
    monkeypatch.setenv("LENSIFY_USER_ADAPTERS", "1")
    fw_dir = tmp_path / ".lensify" / "frameworks"
    fw_dir.mkdir(parents=True)
    (fw_dir / "broken.py").write_text("syntax error !!")
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)
    # Should not raise — bad user adapter must never break discovery
    classes = discover_adapter_classes(parsed, user_dir=fw_dir)
    assert isinstance(classes, list)


# ----- Adapter exception isolation -----

def test_adapter_exception_does_not_break_other_adapters(tmp_path, monkeypatch):
    """One adapter raising during extract() must not kill the rest."""
    (tmp_path / "a.py").write_text("import fastapi\n")
    walk_result = walk(str(tmp_path))
    parsed = parse_all(walk_result.code_files)

    # Patch the fastapi adapter's extract to raise
    from scripts.frameworks._enterprise.fastapi import FastAPIAdapter
    def boom(self, walk_result, parsed_files):
        raise RuntimeError("boom")
    monkeypatch.setattr(FastAPIAdapter, "extract", boom)
    infos = run_adapters(walk_result, parsed, project_root=tmp_path)
    # No crash. Other adapters (none registered yet besides FastAPI) → infos empty.
    assert isinstance(infos, list)


# ----- cap_entries helper -----

def test_cap_entries_respects_absolute_max():
    entries = [FrameworkEntry(kind="x", name=str(i)) for i in range(200)]
    capped = cap_entries(entries, 1000)  # asked for 1000, capped at ABS_MAX
    assert len(capped) == ABSOLUTE_MAX_ENTRIES
