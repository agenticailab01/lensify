"""Core ML/DL framework adapters (PyTorch, Transformers, scikit-learn, HF Datasets).

Each adapter is a ~80-120 LOC module loaded lazily via manifest.json. Shared
helpers live in the parent _util.py (frameworks/_util.py).

R1-R5 perf rules apply uniformly across all packs.
"""
