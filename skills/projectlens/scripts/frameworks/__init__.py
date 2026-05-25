"""ProjectLens framework adapter system (Phase 9 scaffold).

Adapters are framework-aware extractors that contribute domain-specific
sections to the capsule (e.g. ROUTES from FastAPI, COMPONENTS from Vue,
MODELS from PyTorch). They are *lazy-loaded* based on import signatures
detected in the project so the cost is proportional to relevance, not to
the number of adapters that exist.

Hard rules — enforced by the perf test harness:
    1. Hook scripts NEVER import from this package.
    2. Adapters consume the shared WalkResult — they do not walk on their own.
    3. Each adapter's detect() is O(1) (single substring grep).
    4. Each adapter declares a hard cap on entries it surfaces.
    5. Adapters compete for a fixed capsule budget — no growth.
"""
__all__ = ["base", "registry"]
