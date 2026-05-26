"""HuggingFace Transformers adapter — surfaces models, tokenizers, pipelines, trainers.

Triggers on `transformers` imports. Extracts:

    - Model loads:    AutoModel*.from_pretrained("…") / specific *Model.from_pretrained
    - Tokenizer loads: AutoTokenizer.from_pretrained("…")
    - pipeline("task")  calls
    - Trainer(...) / TrainingArguments(...) constructions

The string in `.from_pretrained("X")` is captured into meta["checkpoint"] so
the agent immediately knows which weights the project depends on.

Output: ## TRANSFORMERS capsule section.
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


# Capture: var = (AutoModel*|some*Model).from_pretrained("ckpt", ...)
# AutoTokenizer/AutoFeatureExtractor/AutoProcessor excluded — matched by
# the tokenizer regex below to avoid double-counting.
_MODEL_RE = re.compile(
    r"""(\w+)\s*=\s*("""
    r"""AutoModel\w*|AutoConfig|"""  # Model-like Auto classes only
    r"""\w+Model|"""
    r"""\w+ForSequenceClassification|\w+ForTokenClassification|"""
    r"""\w+ForCausalLM|\w+ForMaskedLM|\w+ForQuestionAnswering|"""
    r"""\w+ForSeq2SeqLM"""
    r""")\s*\.\s*from_pretrained\s*\(\s*['"]([^'"]+)['"]"""
)
_TOKENIZER_RE = re.compile(
    r"""(\w+)\s*=\s*(AutoTokenizer|\w+Tokenizer(?:Fast)?)\s*\.\s*from_pretrained\s*\(\s*['"]([^'"]+)['"]"""
)
_PIPELINE_RE = re.compile(
    r"""(\w+)\s*=\s*pipeline\s*\(\s*['"]([^'"]+)['"]"""
)
_TRAINER_RE = re.compile(
    r"""(\w+)\s*=\s*(Trainer|Seq2SeqTrainer|SFTTrainer|DPOTrainer|PPOTrainer)\s*\("""
)
_TRAINING_ARGS_RE = re.compile(
    r"""(\w+)\s*=\s*(TrainingArguments|Seq2SeqTrainingArguments)\s*\("""
)


class TransformersAdapter(FrameworkAdapter):
    name = "transformers"
    detect_signatures = ("import transformers", "from transformers")
    priority = PRIORITY_HIGH
    max_entries = 25

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["transformers"]

        entries: list[FrameworkEntry] = []
        checkpoints: set[str] = set()

        for rel_path, text in iter_python_with(parsed_files, walk_result, "transformers"):
            for m in _MODEL_RE.finditer(text):
                cp = m.group(3)
                checkpoints.add(cp)
                entries.append(_entry("model", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start()),
                                      checkpoint=cp))
            for m in _TOKENIZER_RE.finditer(text):
                cp = m.group(3)
                checkpoints.add(cp)
                entries.append(_entry("tokenizer", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start()),
                                      checkpoint=cp))
            for m in _PIPELINE_RE.finditer(text):
                entries.append(_entry("pipeline", m.group(1), f"pipeline({m.group(2)!r})",
                                      rel_path, line_of(text, m.start()),
                                      task=m.group(2)))
            for m in _TRAINER_RE.finditer(text):
                entries.append(_entry("trainer", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _TRAINING_ARGS_RE.finditer(text):
                entries.append(_entry("training_args", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["checkpoints"] = sorted(checkpoints)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## TRANSFORMERS"]
        for e in info.entries:
            extra = ""
            if e.meta.get("checkpoint"):
                extra = f" ← `{e.meta['checkpoint']}`"
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}{extra}  ({e.path}:{e.line})")
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
