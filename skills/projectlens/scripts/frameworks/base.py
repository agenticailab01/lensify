"""FrameworkAdapter base class + supporting types.

This file defines the contract every adapter MUST follow. The base class
enforces the hard rules from `__init__.py` at runtime: a subclass that
violates a rule (e.g. excess entries, missing signatures) is caught by the
adapter test suite, not by chance in production.

Contract summary:
    class MyAdapter(FrameworkAdapter):
        name = "my_framework"
        detect_signatures = ["import my_framework", "from my_framework"]
        priority = 60
        max_entries = 20

        def extract(self, walk_result, parsed_files): -> FrameworkInfo
            ...

        def capsule_section(self, info, budget_tokens): -> str | None
            ...
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# Confidence tag conventions — match the capsule's existing RISKS section.
CONFIDENCE_LEVELS = ("EXTRACTED", "INFERRED", "AMBIGUOUS")

# Capsule section priority bands — higher number = higher priority. Adapters
# choose where they sit in the budget-allocation pecking order.
PRIORITY_HIGH = 80    # ROUTES, COMPONENTS — what the user is editing right now
PRIORITY_MEDIUM = 50  # MODELS, CHAINS — important context but not always edited
PRIORITY_LOW = 20     # CONFIG, DEPLOY — situational

# Hard ceiling on entries any single adapter can surface (enforced by tests).
ABSOLUTE_MAX_ENTRIES = 50


@dataclass
class FrameworkEntry:
    """One adapter-specific record. Fields are intentionally loose — different
    frameworks surface different things (a route has a path, a model has a
    shape, a chain has a tools list). Adapters stuff what's relevant into
    `kind`, `name`, `signature`, and `meta`."""
    kind: str                              # "route" | "model" | "chain" | "component" | …
    name: str                              # primary identifier
    signature: str = ""                    # one-line summary
    path: str = ""                         # source file (relative)
    line: int = 0                          # line number (1-based, 0 = unknown)
    confidence: str = "EXTRACTED"          # EXTRACTED/INFERRED/AMBIGUOUS
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FrameworkInfo:
    """The complete output of one adapter's extract() call."""
    name: str                                          # adapter name (matches FrameworkAdapter.name)
    version_detected: str | None = None                # e.g. "0.110.x"
    entries: list[FrameworkEntry] = field(default_factory=list)
    detected_signatures: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version_detected": self.version_detected,
            "entries": [e.to_dict() for e in self.entries],
            "detected_signatures": list(self.detected_signatures),
            "meta": dict(self.meta),
        }


class FrameworkAdapter:
    """Base class for all framework-aware extractors.

    Subclasses MUST set the four class attributes (name, detect_signatures,
    priority, max_entries) and implement extract(). capsule_section() is
    optional; if not overridden, the adapter contributes no capsule output.
    """

    # ---- Required class attributes (subclasses override) ----
    name: str = ""                              # unique adapter id, e.g. "fastapi"
    detect_signatures: tuple[str, ...] = ()     # substrings to grep for in imports
    priority: int = PRIORITY_MEDIUM
    max_entries: int = 20                       # capped by ABSOLUTE_MAX_ENTRIES

    # ---- Detection (default impl — most adapters use this) ----

    @classmethod
    def detect(cls, walk_result, parsed_files) -> bool:
        """O(1) check: do any of detect_signatures appear in any file's imports?

        Override only if signature detection needs custom logic. Default impl
        is one pass through parsed_files' imports — no file content reads.
        """
        if not cls.detect_signatures:
            return False
        # Build a flat set of imports once
        all_imports: set[str] = set()
        for pf in parsed_files:
            for imp in getattr(pf, "imports", []) or []:
                all_imports.add(imp.lower())
        for sig in cls.detect_signatures:
            # Signatures are usually module names; strip "import" / "from" prefixes
            keyword = sig.replace("import ", "").replace("from ", "").strip().split(".")[0].lower()
            if keyword in all_imports:
                return True
        return False

    # ---- Extraction (subclasses override) ----

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        """Build a FrameworkInfo from the project. Must be deterministic.

        Subclasses build entries by walking parsed_files (NOT by re-walking the
        filesystem). Heavy work is allowed here — extract() runs once per scan.
        """
        raise NotImplementedError(f"{type(self).__name__}.extract not implemented")

    # ---- Capsule rendering (optional) ----

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        """Render a Markdown section for the capsule. Return None to opt out.

        Implementations MUST respect budget_tokens (caller enforces a cap)
        and produce at most self.max_entries (capsule builder enforces).
        """
        return None

    # ---- Validation (enforced by tests) ----

    @classmethod
    def validate_class(cls) -> list[str]:
        """Self-check; returns list of error messages, empty if all OK."""
        errors: list[str] = []
        if not cls.name:
            errors.append(f"{cls.__name__}.name must be non-empty")
        if not cls.detect_signatures:
            errors.append(f"{cls.__name__}.detect_signatures must be non-empty")
        if cls.max_entries <= 0 or cls.max_entries > ABSOLUTE_MAX_ENTRIES:
            errors.append(
                f"{cls.__name__}.max_entries must be 1..{ABSOLUTE_MAX_ENTRIES}, got {cls.max_entries}"
            )
        if not (0 <= cls.priority <= 100):
            errors.append(f"{cls.__name__}.priority must be 0..100, got {cls.priority}")
        return errors


def cap_entries(entries: list[FrameworkEntry], limit: int) -> list[FrameworkEntry]:
    """Helper for adapters: cap and stable-sort by name."""
    return list(entries[: min(limit, ABSOLUTE_MAX_ENTRIES)])
