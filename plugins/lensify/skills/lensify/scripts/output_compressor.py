"""Tool-output compression engine (Phase 6).

Detects the *type* of a raw tool output (HTML page / JSON dump / log / Playwright
snapshot / stack trace / diff / tabular / opaque text), then applies a
type-specific compressor. The original is stored on disk; the conversation
receives a structured summary + retrieval handle.

Compression principles:
    - Deterministic: no LLM calls. Pure regex + string manipulation.
    - Reversible: the raw output is preserved on disk, addressable by hash.
    - Honest: every summary states what was kept and what was dropped.
    - Fast: <50ms for outputs up to 1MB.

Closes the v0.4.0 gap with Context Mode by handling the same types of
high-volume tool outputs (Bash dumps, web fetches, log floods).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# Outputs smaller than this byte count are passed through unchanged.
MIN_COMPRESS_BYTES = 2048

# Outputs larger than this are aggressively summarised even within their type.
HUGE_OUTPUT_BYTES = 50_000

OUTPUT_CACHE_DIRNAME = ".lensify-outputs"


@dataclass
class CompressionResult:
    """The outcome of a single compress() call."""
    original_bytes: int
    compressed_bytes: int
    output_type: str                  # detected type label
    summary: str                       # the compressed summary itself
    handle: str | None = None          # path to the raw output on disk, or None if not stored
    bytes_saved: int = 0               # original - compressed (>= 0)

    @property
    def ratio(self) -> float:
        """Compression ratio. Higher = better. 1.0 = no compression."""
        if self.compressed_bytes <= 0:
            return 0.0
        return self.original_bytes / self.compressed_bytes

    def to_dict(self) -> dict:
        return {
            "original_bytes": self.original_bytes,
            "compressed_bytes": self.compressed_bytes,
            "output_type": self.output_type,
            "summary": self.summary,
            "handle": self.handle,
            "bytes_saved": self.bytes_saved,
            "ratio": round(self.ratio, 2),
        }


# ----- Output-type detection -----

_TRACE_MARKERS = (
    "Traceback (most recent call last):",  # Python
    "Error: ", "at ", "    at ",            # JS/Node stack
    "panic: ", "goroutine ",                # Go
    "Exception in thread",                  # Java
)
_DIFF_MARKERS_RE = re.compile(r"^(diff --git|@@ |\+\+\+ |--- )", re.MULTILINE)
_LOG_LINE_RE = re.compile(
    r"^\s*(?:\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}|\[\d{4}-\d{2}-\d{2}|"
    r"(?:INFO|WARN(?:ING)?|ERROR|DEBUG|FATAL|TRACE)\s+)",
    re.MULTILINE,
)
_PLAYWRIGHT_MARKERS = ("- accessibility-tree:", "[role=", "name=", "AriaSnapshot")
_PYTEST_MARKERS = ("== test session starts ==", " passed", " failed in ", "PASSED", "FAILED")
_TABULAR_RE = re.compile(r"^([^\n]+?[\t|,;][^\n]+?[\t|,;][^\n]+)\n", re.MULTILINE)


def detect_output_type(text: str) -> str:
    """Return a label for the output's shape: html | json | log | tabular | trace |
    diff | playwright | pytest | text.
    """
    if not text:
        return "text"
    head = text[:4000]

    # Pytest specifically — long sessions with lots of dots
    if any(m in head for m in _PYTEST_MARKERS):
        return "pytest"

    # Playwright accessibility snapshots
    if any(m in head for m in _PLAYWRIGHT_MARKERS):
        return "playwright"

    # HTML: explicit tag near the top
    stripped = head.lstrip()
    if (stripped.startswith("<!DOCTYPE") or stripped.startswith("<html")
            or "<body" in head or "<head>" in head):
        return "html"

    # JSON: starts with { or [
    stripped_first = stripped[:1]
    if stripped_first in ("{", "["):
        try:
            json.loads(text.strip())
            return "json"
        except (json.JSONDecodeError, ValueError):
            pass  # fall through

    # Diff
    if _DIFF_MARKERS_RE.search(head):
        return "diff"

    # Stack trace
    if any(m in head for m in _TRACE_MARKERS):
        return "trace"

    # Log: many lines look log-shaped
    log_lines = len(_LOG_LINE_RE.findall(head))
    line_count = head.count("\n") + 1
    if log_lines >= 5 and (log_lines / max(line_count, 1)) > 0.3:
        return "log"

    # Tabular: delimited columns on multiple lines
    tab_matches = _TABULAR_RE.findall(head)
    if len(tab_matches) >= 3:
        return "tabular"

    return "text"


# ----- Per-type compressors -----

def _strip_html(html: str) -> str:
    """Best-effort HTML → text. Drops scripts/styles, collapses whitespace."""
    # Remove script/style blocks
    out = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    out = re.sub(r"<style\b[^>]*>.*?</style>", " ", out, flags=re.S | re.I)
    # Remove all tags
    out = re.sub(r"<[^>]+>", " ", out)
    # Decode common entities
    out = (out.replace("&nbsp;", " ").replace("&amp;", "&")
              .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"'))
    # Collapse whitespace
    out = re.sub(r"\s+", " ", out).strip()
    return out


def compress_html(text: str) -> str:
    """Extract title, top headings, first paragraph, summary stats."""
    # Title
    title_m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
    title = title_m.group(1).strip() if title_m else "(no title)"

    # Headings
    headings = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", text, re.S | re.I)[:8]
    headings = [_strip_html(h)[:80] for h in headings if h.strip()]

    # First substantial paragraph
    body_text = _strip_html(text)
    first_para = body_text[:600]

    out = [f"HTML page — title: {title!r}"]
    if headings:
        out.append("Headings:")
        for h in headings:
            out.append(f"  - {h}")
    if first_para:
        out.append(f"Excerpt: {first_para}{'…' if len(body_text) > 600 else ''}")
    out.append(f"Total text length: ~{len(body_text):,} chars")
    return "\n".join(out)


def compress_json(text: str) -> str:
    """Schema + sample items + size."""
    try:
        data = json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        return f"JSON parse failed; raw length {len(text):,} bytes"

    def _schema(value, depth: int = 0) -> str:
        if depth > 3:
            return "..."
        if isinstance(value, dict):
            keys = list(value.keys())[:8]
            return "{" + ", ".join(f"{k}: {_schema(value[k], depth+1)}" for k in keys) + "}"
        if isinstance(value, list):
            if not value:
                return "[]"
            return f"[{_schema(value[0], depth+1)}, ...]"
        if isinstance(value, str):
            return f"str({len(value)})" if len(value) > 40 else f'"{value[:40]}"'
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, (int, float)):
            return "num"
        return type(value).__name__

    schema = _schema(data)
    out = [f"JSON ({type(data).__name__}) — schema: {schema}"]

    if isinstance(data, list):
        out.append(f"Array of {len(data)} items.")
        if data:
            try:
                first = json.dumps(data[0], default=str)[:300]
                out.append(f"First item: {first}")
            except (TypeError, ValueError):
                pass
    elif isinstance(data, dict):
        out.append(f"Object with {len(data)} top-level keys: {list(data.keys())[:12]}")

    return "\n".join(out)


def compress_log(text: str) -> str:
    """Group log lines by level; show first error and counts."""
    lines = text.splitlines()
    levels = {"ERROR": 0, "WARN": 0, "WARNING": 0, "INFO": 0, "DEBUG": 0, "FATAL": 0, "TRACE": 0}
    error_lines: list[str] = []
    for line in lines:
        m = re.search(r"\b(ERROR|WARN(?:ING)?|INFO|DEBUG|FATAL|TRACE)\b", line)
        if m:
            level = m.group(1).upper()
            levels[level] = levels.get(level, 0) + 1
            if level in ("ERROR", "FATAL") and len(error_lines) < 5:
                error_lines.append(line.strip()[:200])
    counts = ", ".join(f"{k}={v}" for k, v in levels.items() if v > 0)
    out = [f"Log output — {len(lines)} lines. Counts: {counts or 'no level keywords'}"]
    if error_lines:
        out.append("First errors:")
        for line in error_lines:
            out.append(f"  {line}")
    return "\n".join(out)


def compress_trace(text: str) -> str:
    """Extract the actual error line + top 3 frames."""
    lines = text.splitlines()
    # Find error message — typically the last non-frame line
    error_line = ""
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("File ", "  File ", "at ", "    at ", "goroutine")):
            continue
        error_line = stripped
        break

    # Top frames
    frames = []
    for line in lines:
        if "File " in line or line.strip().startswith("at "):
            frames.append(line.strip()[:200])
            if len(frames) >= 4:
                break

    out = [f"Stack trace — {len(lines)} lines."]
    if error_line:
        out.append(f"Error: {error_line[:300]}")
    if frames:
        out.append("Top frames:")
        for f in frames:
            out.append(f"  {f}")
    return "\n".join(out)


def compress_diff(text: str) -> str:
    """Summarise a git/unified diff: per-file +/- counts, no context lines."""
    files_changed: dict[str, list[int]] = {}
    current_file: str | None = None
    for line in text.splitlines():
        m = re.match(r"^diff --git a/(\S+) b/(\S+)", line)
        if m:
            current_file = m.group(2)
            files_changed[current_file] = [0, 0]
            continue
        if current_file is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            files_changed[current_file][0] += 1
        elif line.startswith("-") and not line.startswith("---"):
            files_changed[current_file][1] += 1
    out = [f"Diff — {len(files_changed)} files changed."]
    for path, (adds, dels) in list(files_changed.items())[:15]:
        out.append(f"  {path}: +{adds} -{dels}")
    if len(files_changed) > 15:
        out.append(f"  … and {len(files_changed) - 15} more files")
    return "\n".join(out)


def compress_playwright(text: str) -> str:
    """Summarise a Playwright accessibility snapshot — count roles."""
    role_counts: dict[str, int] = {}
    for m in re.finditer(r"\[role=([\w-]+)", text):
        r = m.group(1)
        role_counts[r] = role_counts.get(r, 0) + 1
    # Also: page title if present
    title_m = re.search(r"title=['\"]([^'\"]+)['\"]", text)
    title = title_m.group(1) if title_m else None

    out = ["Playwright snapshot"]
    if title:
        out.append(f"Page title: {title}")
    if role_counts:
        top = sorted(role_counts.items(), key=lambda kv: kv[1], reverse=True)[:8]
        out.append("Top elements: " + ", ".join(f"{r}×{n}" for r, n in top))
    out.append(f"Total accessibility nodes: ~{sum(role_counts.values())}")
    return "\n".join(out)


def compress_pytest(text: str) -> str:
    """pytest-like output: capture totals + first few failing tests."""
    passed_m = re.search(r"(\d+)\s+passed", text)
    failed_m = re.search(r"(\d+)\s+failed", text)
    error_m = re.search(r"(\d+)\s+error", text)
    skipped_m = re.search(r"(\d+)\s+skipped", text)
    failing = re.findall(r"^FAILED\s+(\S+::\S+)", text, re.MULTILINE)[:5]
    parts = []
    if passed_m: parts.append(f"{passed_m.group(1)} passed")
    if failed_m: parts.append(f"**{failed_m.group(1)} failed**")
    if error_m:  parts.append(f"{error_m.group(1)} errors")
    if skipped_m: parts.append(f"{skipped_m.group(1)} skipped")
    out = ["pytest output — " + (", ".join(parts) if parts else "no totals detected")]
    if failing:
        out.append("Failing tests:")
        for n in failing:
            out.append(f"  - {n}")
    return "\n".join(out)


def compress_tabular(text: str) -> str:
    """Summarise delimited tabular text: header + sample rows + row count."""
    lines = text.splitlines()
    if not lines:
        return "Empty tabular output."
    header = lines[0]
    sample = lines[1:4]
    out = [
        f"Tabular output — {len(lines)} rows.",
        f"Header: {header[:200]}",
    ]
    if sample:
        out.append("Sample rows:")
        for row in sample:
            out.append(f"  {row[:200]}")
    return "\n".join(out)


def compress_text(text: str) -> str:
    """Generic fallback: head + middle + tail snippet."""
    n = len(text)
    if n <= 1500:
        return text
    head = text[:500]
    mid_start = max(0, n // 2 - 100)
    middle = text[mid_start: mid_start + 200]
    tail = text[-500:]
    return (
        f"Long text output ({n:,} bytes). Head/middle/tail snippets:\n\n"
        f"--- head ---\n{head}\n"
        f"--- middle (offset {mid_start}) ---\n{middle}\n"
        f"--- tail ---\n{tail}"
    )


_COMPRESSORS = {
    "html": compress_html,
    "json": compress_json,
    "log": compress_log,
    "trace": compress_trace,
    "diff": compress_diff,
    "playwright": compress_playwright,
    "pytest": compress_pytest,
    "tabular": compress_tabular,
    "text": compress_text,
}


def compress(text: str, *, project_root: str | Path | None = None,
             store: bool = True, min_bytes: int = MIN_COMPRESS_BYTES) -> CompressionResult:
    """Top-level compression call.

    Returns a CompressionResult. If the input is shorter than min_bytes, returns
    a pass-through result (no compression applied, no handle stored).
    """
    text = text or ""
    original_bytes = len(text.encode("utf-8"))
    if original_bytes < min_bytes:
        return CompressionResult(
            original_bytes=original_bytes,
            compressed_bytes=original_bytes,
            output_type="passthrough",
            summary=text,
            handle=None,
            bytes_saved=0,
        )

    output_type = detect_output_type(text)
    compressor = _COMPRESSORS.get(output_type, compress_text)
    summary = compressor(text)

    # For huge outputs, also strip the summary further by running through compress_text
    if original_bytes > HUGE_OUTPUT_BYTES and len(summary) > 1500:
        summary = summary[:1200] + "\n…[summary truncated]…"

    handle: str | None = None
    if store and project_root is not None:
        try:
            handle = _store_raw(text, Path(project_root))
        except OSError:
            handle = None

    compressed_bytes = len(summary.encode("utf-8"))
    return CompressionResult(
        original_bytes=original_bytes,
        compressed_bytes=compressed_bytes,
        output_type=output_type,
        summary=summary,
        handle=handle,
        bytes_saved=max(0, original_bytes - compressed_bytes),
    )


def _store_raw(text: str, project_root: Path) -> str:
    """Write the raw output to .lensify-outputs/<sha256-12>.txt."""
    cache_dir = project_root / OUTPUT_CACHE_DIRNAME
    cache_dir.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    target = cache_dir / f"{sha}.txt"
    if not target.exists():
        target.write_text(text, encoding="utf-8")
    return str(target)


def format_for_agent(result: CompressionResult) -> str:
    """Render a CompressionResult as the additionalContext string for the hook.

    Includes the summary, byte counts, type label, and (if stored) the retrieval
    handle so the agent can fetch the full output only if needed.
    """
    if result.output_type == "passthrough":
        return ""

    lines = [
        f"[Lensify] Tool output ({result.original_bytes:,} bytes, "
        f"detected as `{result.output_type}`) — compressed to "
        f"{result.compressed_bytes:,} bytes ({result.ratio:.1f}× ratio).",
        "",
        "Summary:",
        result.summary,
    ]
    if result.handle:
        rel = os.path.relpath(result.handle, start=os.path.dirname(os.path.dirname(result.handle)))
        lines.extend([
            "",
            f"Full raw output saved to `{result.handle}`. "
            "Read it back only if the summary is insufficient.",
        ])
    return "\n".join(lines)


def is_disabled() -> bool:
    """Opt out via LENSIFY_COMPRESS_OUTPUT=0."""
    val = os.environ.get("LENSIFY_COMPRESS_OUTPUT")
    if val is None:
        # Falls back to the global LENSIFY_DEDUP switch
        val = os.environ.get("LENSIFY_DEDUP")
    return val in ("0", "false", "no", "off")
