"""MLflow adapter — surfaces experiments, runs, log calls, model flavors.

Triggers on `mlflow` imports. Extracts:

    - mlflow.set_experiment("name") — captures experiment names
    - mlflow.set_tracking_uri("uri") — tracking server URI
    - mlflow.start_run(run_name=..., nested=...) — run starts
    - log_param / log_metric / log_artifact call counts
    - mlflow.{flavor}.log_model(...) — captures the flavor (sklearn,
      pytorch, tensorflow, transformers, langchain, …)

Output: ## MLFLOW capsule section.
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


_EXPERIMENT_RE = re.compile(
    r"""\bmlflow\s*\.\s*set_experiment\s*\(\s*(?:experiment_name\s*=\s*)?['"]([^'"]+)['"]"""
)
_TRACKING_URI_RE = re.compile(
    r"""\bmlflow\s*\.\s*set_tracking_uri\s*\(\s*['"]([^'"]+)['"]"""
)
_START_RUN_RE = re.compile(r"""\bmlflow\s*\.\s*start_run\s*\(([^)]*)\)""", re.S)
_RUN_NAME_RE = re.compile(r"""run_name\s*=\s*['"]([^'"]+)['"]""")
_LOG_PARAM_RE = re.compile(r"""\bmlflow\s*\.\s*log_param\w*\s*\(""")
_LOG_METRIC_RE = re.compile(r"""\bmlflow\s*\.\s*log_metric\w*\s*\(""")
_LOG_ARTIFACT_RE = re.compile(r"""\bmlflow\s*\.\s*log_artifact\w*\s*\(""")
_LOG_MODEL_RE = re.compile(r"""\bmlflow\s*\.\s*(\w+)\s*\.\s*log_model\s*\(""")


class MLflowAdapter(FrameworkAdapter):
    name = "mlflow"
    detect_signatures = ("import mlflow", "from mlflow")
    priority = PRIORITY_HIGH
    max_entries = 20

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["mlflow"]

        entries: list[FrameworkEntry] = []
        experiments: set[str] = set()
        tracking_uris: set[str] = set()
        run_names: set[str] = set()
        log_param_count = 0
        log_metric_count = 0
        log_artifact_count = 0
        model_flavors: set[str] = set()

        for rel_path, text in iter_python_with(parsed_files, walk_result, "mlflow"):
            for m in _EXPERIMENT_RE.finditer(text):
                name = m.group(1)
                experiments.add(name)
                entries.append(_entry("experiment", name,
                                      f"set_experiment({name!r})",
                                      rel_path, line_of(text, m.start())))
            for m in _TRACKING_URI_RE.finditer(text):
                tracking_uris.add(m.group(1))
            for m in _START_RUN_RE.finditer(text):
                body = m.group(1) or ""
                name_m = _RUN_NAME_RE.search(body)
                run_name = name_m.group(1) if name_m else "(anon)"
                if name_m:
                    run_names.add(run_name)
                entries.append(_entry("run", run_name,
                                      f"start_run(name={run_name!r})",
                                      rel_path, line_of(text, m.start())))
            for m in _LOG_MODEL_RE.finditer(text):
                flavor = m.group(1)
                model_flavors.add(flavor)
                entries.append(_entry("model", flavor,
                                      f"mlflow.{flavor}.log_model()",
                                      rel_path, line_of(text, m.start()),
                                      flavor=flavor))
            log_param_count += len(_LOG_PARAM_RE.findall(text))
            log_metric_count += len(_LOG_METRIC_RE.findall(text))
            log_artifact_count += len(_LOG_ARTIFACT_RE.findall(text))

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["experiments"] = sorted(experiments)
        info.meta["tracking_uris"] = sorted(tracking_uris)
        info.meta["model_flavors"] = sorted(model_flavors)
        info.meta["ops"] = {
            "log_param": log_param_count,
            "log_metric": log_metric_count,
            "log_artifact": log_artifact_count,
        }
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("ops", {}).get("log_metric"):
            return None
        lines = ["## MLFLOW"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        uris = info.meta.get("tracking_uris") or []
        if uris:
            lines.append(f"- tracking URI: {', '.join(uris[:2])}")
        flavors = info.meta.get("model_flavors") or []
        if flavors:
            lines.append(f"- model flavors: {', '.join(flavors)}")
        ops = info.meta.get("ops") or {}
        nonzero = {k: v for k, v in ops.items() if v}
        if nonzero:
            shown = ", ".join(f"{k}×{v}" for k, v in nonzero.items())
            lines.append(f"- ops: {shown}")
        return truncate("\n".join(lines), budget_tokens)


def _entry(kind: str, name: str, sig: str, rel_path: str, line: int,
           **meta) -> FrameworkEntry:
    return FrameworkEntry(
        kind=kind, name=name, signature=sig,
        path=rel_path, line=line, confidence="EXTRACTED",
        meta={"class": sig, **meta},
    )
