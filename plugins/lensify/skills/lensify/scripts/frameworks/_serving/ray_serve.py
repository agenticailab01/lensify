"""Ray Serve adapter — surfaces deployments, ingress, run entrypoints.

Triggers on `ray` imports (broad signature) — but only emits entries when
the file actually uses `serve.*` patterns. This keeps the adapter quiet on
ray-but-not-ray-serve projects (Ray Train, Ray Tune, Ray Data, etc.).

Extracts:

    - @serve.deployment-decorated classes/functions
    - @serve.ingress(app) decorators (FastAPI integration)
    - serve.run(...) entrypoints (model deployment)
    - DeploymentHandle bindings (`.bind(...)`)

Output: ## RAY-SERVE capsule section.
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


# Allow any number of intervening decorator lines between @serve.deployment
# and the class/def — common pattern when combining with @serve.ingress.
_DEPLOYMENT_RE = re.compile(
    r"""@\s*serve\s*\.\s*deployment\b[^\n]*\n"""
    r"""(?:\s*@[^\n]*\n)*"""
    r"""\s*(?:class|(?:async\s+)?def)\s+(\w+)"""
)
_INGRESS_RE = re.compile(
    r"""@\s*serve\s*\.\s*ingress\s*\(\s*(\w+)"""
)
_RUN_RE = re.compile(r"""\bserve\s*\.\s*run\s*\(""")
_BIND_RE = re.compile(r"""(\w+)\s*=\s*(\w+)\s*\.\s*bind\s*\(""")
_SERVE_IMPORT_RE = re.compile(r"""\bfrom\s+ray\s+import\s+serve\b|\bray\.serve\b""")


class RayServeAdapter(FrameworkAdapter):
    name = "ray_serve"
    # Signature is broad (just "ray"), but we filter inside extract().
    detect_signatures = ("import ray", "from ray")
    priority = PRIORITY_HIGH
    max_entries = 15

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["ray.serve"]

        entries: list[FrameworkEntry] = []
        run_files: set[str] = set()

        for rel_path, text in iter_python_with(parsed_files, walk_result, "ray"):
            # Only emit anything if the file actually uses Ray Serve
            if not _SERVE_IMPORT_RE.search(text):
                continue
            for m in _DEPLOYMENT_RE.finditer(text):
                entries.append(FrameworkEntry(
                    kind="deployment",
                    name=m.group(1),
                    signature="@serve.deployment",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"class": m.group(1)},
                ))
            for m in _INGRESS_RE.finditer(text):
                entries.append(FrameworkEntry(
                    kind="ingress",
                    name=m.group(1),
                    signature="@serve.ingress",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"app": m.group(1)},
                ))
            for m in _BIND_RE.finditer(text):
                entries.append(FrameworkEntry(
                    kind="binding",
                    name=m.group(1),
                    signature=f"{m.group(2)}.bind",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"target": m.group(2)},
                ))
            if _RUN_RE.search(text):
                run_files.add(rel_path)

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["run_files"] = sorted(run_files)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("run_files"):
            return None
        lines = ["## RAY-SERVE"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        run = info.meta.get("run_files") or []
        if run:
            lines.append(f"- serve.run() in: {', '.join(run[:3])}")
        return truncate("\n".join(lines), budget_tokens)
