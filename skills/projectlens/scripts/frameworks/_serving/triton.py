"""NVIDIA Triton client adapter — surfaces inference server clients + models.

Triggers on `tritonclient` imports (the official Python client SDK). Extracts:

    - tritonclient.http.InferenceServerClient(url=…) constructions
    - tritonclient.grpc.InferenceServerClient(url=…) constructions
    - InferInput(name, shape, dtype) — captured inputs
    - InferRequestedOutput(name) — captured outputs
    - .infer(model_name=…) / .async_infer(model_name=…) calls — model refs

Output: ## TRITON capsule section showing clients, referenced models, and
the I/O shape of inference calls.
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


_CLIENT_RE = re.compile(
    r"""(\w+)\s*=\s*(?:(?:tritonclient\.)?(?:http|grpc|httpclient|grpcclient)\s*\.\s*)?"""
    r"""InferenceServerClient\s*\(\s*(?:url\s*=\s*)?['"]?([^'",)]+)?"""
)
_INFER_INPUT_RE = re.compile(
    r"""InferInput\s*\(\s*['"]([^'"]+)['"]"""
)
_INFER_OUTPUT_RE = re.compile(
    r"""InferRequestedOutput\s*\(\s*['"]([^'"]+)['"]"""
)
_INFER_CALL_RE = re.compile(
    r"""\.\s*(?:async_)?infer\s*\(\s*(?:model_name\s*=\s*)?['"]([^'"]+)['"]"""
)


class TritonAdapter(FrameworkAdapter):
    name = "triton"
    detect_signatures = ("import tritonclient", "from tritonclient")
    priority = PRIORITY_HIGH
    max_entries = 15

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["tritonclient"]

        entries: list[FrameworkEntry] = []
        inputs: set[str] = set()
        outputs: set[str] = set()
        models: set[str] = set()

        for rel_path, text in iter_python_with(parsed_files, walk_result, "tritonclient"):
            for m in _CLIENT_RE.finditer(text):
                url = (m.group(2) or "").strip().rstrip("'\"")
                entries.append(FrameworkEntry(
                    kind="client",
                    name=m.group(1),
                    signature="InferenceServerClient",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={"class": "InferenceServerClient", "url": url},
                ))
            for m in _INFER_INPUT_RE.finditer(text):
                inputs.add(m.group(1))
            for m in _INFER_OUTPUT_RE.finditer(text):
                outputs.add(m.group(1))
            for m in _INFER_CALL_RE.finditer(text):
                models.add(m.group(1))

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["models_referenced"] = sorted(models)
        info.meta["inputs"] = sorted(inputs)
        info.meta["outputs"] = sorted(outputs)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("models_referenced"):
            return None
        lines = ["## TRITON"]
        for e in info.entries:
            url = e.meta.get("url") or "?"
            url_str = f" → {url}" if url and url != "?" else ""
            lines.append(f"- client `{e.name}`{url_str}  ({e.path}:{e.line})")
        models = info.meta.get("models_referenced") or []
        if models:
            lines.append(f"- models: {', '.join(models[:6])}")
        inputs = info.meta.get("inputs") or []
        outputs = info.meta.get("outputs") or []
        if inputs or outputs:
            lines.append(f"- I/O: in={inputs[:4]} out={outputs[:4]}")
        return truncate("\n".join(lines), budget_tokens)
