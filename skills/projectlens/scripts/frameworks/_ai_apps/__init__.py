"""AI-app framework adapters (LangChain, LlamaIndex, LangGraph, Pydantic AI, DSPy).

This package is intentionally minimal — each adapter is a self-contained
~80 LOC module loaded only when its signature matches. The `_util` module
holds two helpers shared by all 5 adapters so each stays small.

R1-R5 perf rules apply: detect() never opens files, adapters are loaded
lazily via manifest.json, and the per-adapter capsule budget never exceeds
its slice of the framework section budget.
"""
