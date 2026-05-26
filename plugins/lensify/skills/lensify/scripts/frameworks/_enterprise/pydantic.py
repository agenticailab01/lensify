"""Pydantic adapter — surfaces models, fields, validators.

Triggers on `pydantic` imports. Extracts:

    - Classes inheriting from BaseModel / RootModel
    - Field definitions per model (counts)
    - @field_validator / @model_validator / @validator (legacy) decorators
    - model_config = ConfigDict(...) settings

Output: ## PYDANTIC capsule section showing models with field counts and
validators.
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


# Class inheriting BaseModel / RootModel / GenericModel
_MODEL_RE = re.compile(
    r"""class\s+(\w+)\s*\(\s*(?:[\w.]+\s*,\s*)*([\w.]+)\s*\)\s*:"""
)
_BASES_OK = re.compile(r"""(^|\.)(BaseModel|RootModel|GenericModel)$""")
# Field assignment inside a class body: `name: type = Field(...)`
_FIELD_RE = re.compile(
    r"""^\s+(\w+)\s*:\s*[^\n=]+(?:=\s*(?:Field\s*\(|[^\n]+))?$""",
    re.M,
)
_VALIDATOR_RE = re.compile(
    r"""@\s*(field_validator|model_validator|validator|root_validator)\b"""
)
_CONFIG_RE = re.compile(r"""model_config\s*=\s*ConfigDict\s*\(""")


class PydanticAdapter(FrameworkAdapter):
    name = "pydantic"
    detect_signatures = ("import pydantic", "from pydantic")
    priority = PRIORITY_HIGH
    max_entries = 30

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["pydantic"]

        entries: list[FrameworkEntry] = []
        validator_counts: dict[str, int] = {}
        models_with_config: list[str] = []

        for rel_path, text in iter_python_with(parsed_files, walk_result, "pydantic"):
            for m in _MODEL_RE.finditer(text):
                cls = m.group(1)
                parent = m.group(2)
                if not _BASES_OK.search(parent):
                    continue
                # Walk forward to find the end of this class (next class def at same indent or EOF)
                body_start = m.end()
                # Heuristic: take ~2 KB or until next "class " at column 0
                body = text[body_start: body_start + 2500]
                next_cls = re.search(r"\nclass\s+\w", body)
                if next_cls:
                    body = body[: next_cls.start()]
                field_count = len(_FIELD_RE.findall(body))
                has_config = bool(_CONFIG_RE.search(body))
                if has_config:
                    models_with_config.append(cls)
                entries.append(FrameworkEntry(
                    kind="model",
                    name=cls,
                    signature=f"class {cls}({parent})",
                    path=rel_path, line=line_of(text, m.start()),
                    confidence="EXTRACTED",
                    meta={
                        "class": cls,
                        "base": parent,
                        "fields": field_count,
                        "has_config": has_config,
                    },
                ))
            for m in _VALIDATOR_RE.finditer(text):
                v = m.group(1)
                validator_counts[v] = validator_counts.get(v, 0) + 1

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["validators"] = dict(sorted(validator_counts.items(),
                                                key=lambda kv: -kv[1]))
        info.meta["models_with_config"] = sorted(models_with_config)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## PYDANTIC"]
        for e in info.entries:
            fields = e.meta.get("fields", 0)
            cfg = " · config" if e.meta.get("has_config") else ""
            lines.append(f"- model `{e.name}` — {fields} fields{cfg}  ({e.path}:{e.line})")
        validators = info.meta.get("validators") or {}
        if validators:
            shown = ", ".join(f"{k}×{v}" for k, v in list(validators.items())[:4])
            lines.append(f"- validators: {shown}")
        return truncate("\n".join(lines), budget_tokens)
