"""HuggingFace Datasets adapter — surfaces dataset loads + transforms.

Triggers on `datasets` imports (HuggingFace, not the stdlib). Extracts:

    - `load_dataset("name", ...)` calls — captures dataset name into meta
    - `Dataset.from_*(...)` constructions (from_dict, from_pandas, from_csv, …)
    - `.map(fn)`, `.filter(fn)`, `.select_columns([...])` transforms
    - `DatasetDict(...)` constructions

Output: ## DATASETS capsule section.

Note: the manifest entry uses signature "import datasets" / "from datasets"
which is unambiguous in practice — the stdlib lacks `import datasets`.
"""
from __future__ import annotations

import re

try:
    from ..base import (
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_MEDIUM, cap_entries,
    )
    from .._util import iter_python_with, truncate, line_of
except ImportError:
    from base import (  # type: ignore[no-redef]
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_MEDIUM, cap_entries,
    )
    from _util import iter_python_with, truncate, line_of  # type: ignore[no-redef]


_LOAD_DATASET_RE = re.compile(
    r"""(\w+)\s*=\s*load_dataset\s*\(\s*['"]([^'"]+)['"]"""
)
_FROM_RE = re.compile(
    r"""(\w+)\s*=\s*Dataset\.\s*(from_dict|from_pandas|from_csv|from_json|"""
    r"""from_parquet|from_generator|from_list|from_text)\s*\("""
)
_DICT_RE = re.compile(r"""(\w+)\s*=\s*DatasetDict\s*\(""")
_MAP_RE = re.compile(r"""\.\s*map\s*\(""")
_FILTER_RE = re.compile(r"""\.\s*filter\s*\(""")


class DatasetsHFAdapter(FrameworkAdapter):
    name = "datasets_hf"
    detect_signatures = ("import datasets", "from datasets")
    priority = PRIORITY_MEDIUM
    max_entries = 20

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["datasets"]

        entries: list[FrameworkEntry] = []
        names: set[str] = set()
        map_files: set[str] = set()
        filter_files: set[str] = set()

        for rel_path, text in iter_python_with(parsed_files, walk_result, "datasets"):
            for m in _LOAD_DATASET_RE.finditer(text):
                ds_name = m.group(2)
                names.add(ds_name)
                entries.append(_entry("dataset", m.group(1), f"load_dataset({ds_name!r})",
                                      rel_path, line_of(text, m.start()),
                                      dataset_name=ds_name))
            for m in _FROM_RE.finditer(text):
                entries.append(_entry("dataset", m.group(1), f"Dataset.{m.group(2)}",
                                      rel_path, line_of(text, m.start())))
            for m in _DICT_RE.finditer(text):
                entries.append(_entry("dataset_dict", m.group(1), "DatasetDict",
                                      rel_path, line_of(text, m.start())))
            if _MAP_RE.search(text):
                map_files.add(rel_path)
            if _FILTER_RE.search(text):
                filter_files.add(rel_path)

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["dataset_names"] = sorted(names)
        info.meta["map_in"] = sorted(map_files)
        info.meta["filter_in"] = sorted(filter_files)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## DATASETS"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        transforms = []
        if info.meta.get("map_in"):
            transforms.append(f".map in {len(info.meta['map_in'])} file(s)")
        if info.meta.get("filter_in"):
            transforms.append(f".filter in {len(info.meta['filter_in'])} file(s)")
        if transforms:
            lines.append(f"- transforms: {', '.join(transforms)}")
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
