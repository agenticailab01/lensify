"""vLLM adapter — surfaces inference engines, sampling configs, server entries.

Triggers on `vllm` imports. Extracts:

    - LLM(model="checkpoint", ...) constructors — captures the checkpoint
      so the capsule shows which weights are actually served
    - AsyncLLMEngine / LLMEngine constructions
    - SamplingParams(...) configurations
    - api_server.run_server(...) entry points (OpenAI-compatible server)

Output: ## VLLM capsule section.
"""
from __future__ import annotations

import re

try:
    from ..base import (
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )
    from .._util import iter_python_with, truncate, line_of
except ImportError:
    from base import (  # type: ignore[no-redef]
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )
    from _util import iter_python_with, truncate, line_of  # type: ignore[no-redef]


# Capture `var = LLM(model="X", ...)` or `LLM("X", ...)`
_LLM_RE = re.compile(
    r"""(\w+)\s*=\s*LLM\s*\(\s*(?:model\s*=\s*)?['"]([^'"]+)['"]"""
)
_ENGINE_RE = re.compile(
    r"""(\w+)\s*=\s*(AsyncLLMEngine|LLMEngine)\s*\."""
)
_SAMPLING_RE = re.compile(
    r"""(\w+)\s*=\s*SamplingParams\s*\("""
)
_SERVER_RE = re.compile(r"""\b(api_server\.run_server|run_server)\s*\(""")


class VLLMAdapter(FrameworkAdapter):
    name = "vllm"
    detect_signatures = ("import vllm", "from vllm")
    priority = PRIORITY_HIGH
    max_entries = 15

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["vllm"]

        entries: list[FrameworkEntry] = []
        checkpoints: set[str] = set()
        server_files: set[str] = set()

        for rel_path, text in iter_python_with(parsed_files, walk_result, "vllm"):
            for m in _LLM_RE.finditer(text):
                cp = m.group(2)
                checkpoints.add(cp)
                entries.append(_entry("engine", m.group(1), "LLM",
                                      rel_path, line_of(text, m.start()),
                                      checkpoint=cp))
            for m in _ENGINE_RE.finditer(text):
                entries.append(_entry("engine", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _SAMPLING_RE.finditer(text):
                entries.append(_entry("sampling", m.group(1), "SamplingParams",
                                      rel_path, line_of(text, m.start())))
            if _SERVER_RE.search(text):
                server_files.add(rel_path)

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["checkpoints"] = sorted(checkpoints)
        info.meta["server_files"] = sorted(server_files)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("server_files"):
            return None
        lines = ["## VLLM"]
        for e in info.entries:
            extra = ""
            if e.meta.get("checkpoint"):
                extra = f" ← `{e.meta['checkpoint']}`"
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}{extra}  ({e.path}:{e.line})")
        sf = info.meta.get("server_files") or []
        if sf:
            lines.append(f"- OpenAI-compatible server in: {', '.join(sf[:3])}")
        return truncate("\n".join(lines), budget_tokens)


def _entry(kind: str, name: str, cls: str, rel_path: str, line: int,
           **meta) -> FrameworkEntry:
    base_meta = {"class": cls}
    base_meta.update(meta)
    return FrameworkEntry(
        kind=kind, name=name, signature=cls,
        path=rel_path, line=line, confidence="EXTRACTED",
        meta=base_meta,
    )
