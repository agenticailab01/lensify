"""PyTorch adapter — surfaces models, optimizers, losses, dataloaders.

Triggers on `torch` imports. Extracts the structural skeleton an AI engineer
needs to reason about a deep learning project:

    - nn.Module subclasses (model architectures)
    - torch.optim instantiations (Adam, SGD, AdamW, …)
    - Loss function instantiations (CrossEntropyLoss, MSELoss, …)
    - DataLoader constructions
    - Detected training loop pattern (loss.backward + optimizer.step)

Output: ## TORCH capsule section.
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


_MODULE_RE = re.compile(
    r"""class\s+(\w+)\s*\(\s*(?:nn\.)?(?:torch\.nn\.)?Module\s*\)"""
)
_OPTIMIZER_RE = re.compile(
    r"""(\w+)\s*=\s*(?:torch\.)?optim\.(Adam|AdamW|SGD|RMSprop|Adagrad|Adadelta|Adamax|NAdam|RAdam|LBFGS)\s*\("""
)
_LOSS_RE = re.compile(
    r"""(\w+)\s*=\s*(?:torch\.)?nn\.(CrossEntropyLoss|MSELoss|L1Loss|BCELoss|"""
    r"""BCEWithLogitsLoss|NLLLoss|KLDivLoss|HuberLoss|SmoothL1Loss|"""
    r"""CTCLoss|TripletMarginLoss|CosineEmbeddingLoss)\s*\("""
)
_DATALOADER_RE = re.compile(
    r"""(\w+)\s*=\s*(?:torch\.utils\.data\.)?DataLoader\s*\("""
)
_BACKWARD_RE = re.compile(r"""\.backward\s*\(""")
_OPTIM_STEP_RE = re.compile(r"""\.\s*step\s*\(\s*\)""")


class PyTorchAdapter(FrameworkAdapter):
    name = "pytorch"
    detect_signatures = ("import torch", "from torch")
    priority = PRIORITY_HIGH
    max_entries = 30

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["torch"]

        entries: list[FrameworkEntry] = []
        training_files: set[str] = set()

        for rel_path, text in iter_python_with(parsed_files, walk_result, "torch"):
            for m in _MODULE_RE.finditer(text):
                entries.append(_entry("model", m.group(1), "nn.Module",
                                      rel_path, line_of(text, m.start())))
            for m in _OPTIMIZER_RE.finditer(text):
                entries.append(_entry("optimizer", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _LOSS_RE.finditer(text):
                entries.append(_entry("loss", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _DATALOADER_RE.finditer(text):
                entries.append(_entry("dataloader", m.group(1), "DataLoader",
                                      rel_path, line_of(text, m.start())))
            # Heuristic: training loop = .backward() AND .step() in same file
            if _BACKWARD_RE.search(text) and _OPTIM_STEP_RE.search(text):
                training_files.add(rel_path)

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["training_loops"] = sorted(training_files)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("training_loops"):
            return None
        lines = ["## TORCH"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        loops = info.meta.get("training_loops") or []
        if loops:
            lines.append(f"- training loops in: {', '.join(loops[:5])}")
        return truncate("\n".join(lines), budget_tokens)


def _entry(kind: str, name: str, cls: str, rel_path: str, line: int) -> FrameworkEntry:
    return FrameworkEntry(
        kind=kind, name=name, signature=cls,
        path=rel_path, line=line, confidence="EXTRACTED",
        meta={"class": cls},
    )
