"""Tests for the _ml_core adapter pack — PyTorch, Transformers, scikit-learn,
HuggingFace Datasets."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "lensify"
sys.path.insert(0, str(SCRIPTS))

from scripts.walker import walk  # noqa: E402
from scripts.ast_parser import parse_all  # noqa: E402
from scripts.frameworks._ml_core.pytorch import PyTorchAdapter  # noqa: E402
from scripts.frameworks._ml_core.transformers import TransformersAdapter  # noqa: E402
from scripts.frameworks._ml_core.sklearn import SklearnAdapter  # noqa: E402
from scripts.frameworks._ml_core.datasets_hf import DatasetsHFAdapter  # noqa: E402


def _walk(p):
    wr = walk(str(p))
    return wr, parse_all(wr.code_files)


# ---------------- PyTorch ----------------

@pytest.fixture
def pytorch_project(tmp_path):
    (tmp_path / "model.py").write_text(
        "import torch\n"
        "import torch.nn as nn\n"
        "from torch.utils.data import DataLoader\n"
        "\n"
        "class Encoder(nn.Module):\n"
        "    def __init__(self):\n"
        "        super().__init__()\n"
        "        self.fc = nn.Linear(10, 5)\n"
        "\n"
        "class Decoder(nn.Module):\n"
        "    pass\n"
        "\n"
        "model = Encoder()\n"
        "loss_fn = nn.CrossEntropyLoss()\n"
        "optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)\n"
        "loader = DataLoader(None, batch_size=32)\n"
        "\n"
        "for batch in loader:\n"
        "    out = model(batch)\n"
        "    loss = loss_fn(out, batch)\n"
        "    loss.backward()\n"
        "    optimizer.step()\n"
    )
    return tmp_path


def test_pytorch_detect(pytorch_project):
    wr, parsed = _walk(pytorch_project)
    assert PyTorchAdapter.detect(wr, parsed) is True


def test_pytorch_extract(pytorch_project):
    wr, parsed = _walk(pytorch_project)
    info = PyTorchAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    names = {e.name for e in info.entries}
    assert "model" in kinds
    assert "optimizer" in kinds
    assert "loss" in kinds
    assert "dataloader" in kinds
    assert "Encoder" in names
    assert "Decoder" in names
    assert info.meta["training_loops"] == ["model.py"]


def test_pytorch_capsule(pytorch_project):
    wr, parsed = _walk(pytorch_project)
    info = PyTorchAdapter().extract(wr, parsed)
    section = PyTorchAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "TORCH" in section
    assert "Encoder" in section
    assert "AdamW" in section
    assert "training loops" in section


# ---------------- Transformers ----------------

@pytest.fixture
def transformers_project(tmp_path):
    (tmp_path / "finetune.py").write_text(
        "from transformers import (\n"
        "    AutoModelForSequenceClassification, AutoTokenizer,\n"
        "    Trainer, TrainingArguments, pipeline,\n"
        ")\n"
        "\n"
        "tok = AutoTokenizer.from_pretrained('bert-base-uncased')\n"
        "model = AutoModelForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)\n"
        "args = TrainingArguments(output_dir='./out', num_train_epochs=3)\n"
        "trainer = Trainer(model=model, args=args)\n"
        "sentiment = pipeline('sentiment-analysis')\n"
    )
    return tmp_path


def test_transformers_detect(transformers_project):
    wr, parsed = _walk(transformers_project)
    assert TransformersAdapter.detect(wr, parsed) is True


def test_transformers_extract(transformers_project):
    wr, parsed = _walk(transformers_project)
    info = TransformersAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    assert "model" in kinds
    assert "tokenizer" in kinds
    assert "trainer" in kinds
    assert "training_args" in kinds
    assert "pipeline" in kinds
    assert "bert-base-uncased" in info.meta["checkpoints"]


def test_transformers_capsule(transformers_project):
    wr, parsed = _walk(transformers_project)
    info = TransformersAdapter().extract(wr, parsed)
    section = TransformersAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "TRANSFORMERS" in section
    assert "bert-base-uncased" in section
    assert "sentiment-analysis" in section


# ---------------- scikit-learn ----------------

@pytest.fixture
def sklearn_project(tmp_path):
    (tmp_path / "pipeline.py").write_text(
        "from sklearn.linear_model import LogisticRegression\n"
        "from sklearn.ensemble import RandomForestClassifier\n"
        "from sklearn.pipeline import Pipeline, make_pipeline\n"
        "from sklearn.preprocessing import StandardScaler\n"
        "from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score\n"
        "\n"
        "X, y = None, None\n"
        "X_train, X_test, y_train, y_test = train_test_split(X, y)\n"
        "scaler = StandardScaler()\n"
        "clf = LogisticRegression(max_iter=1000)\n"
        "rf = RandomForestClassifier(n_estimators=100)\n"
        "pipe = make_pipeline(scaler, clf)\n"
        "grid = GridSearchCV(pipe, param_grid={})\n"
        "scores = cross_val_score(pipe, X, y)\n"
    )
    return tmp_path


def test_sklearn_detect(sklearn_project):
    wr, parsed = _walk(sklearn_project)
    assert SklearnAdapter.detect(wr, parsed) is True


def test_sklearn_extract(sklearn_project):
    wr, parsed = _walk(sklearn_project)
    info = SklearnAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    classes = {e.meta["class"] for e in info.entries}
    assert "estimator" in kinds
    assert "pipeline" in kinds
    assert "search" in kinds
    assert "LogisticRegression" in classes
    assert "RandomForestClassifier" in classes
    assert "StandardScaler" in classes
    assert "GridSearchCV" in classes
    assert info.meta["train_test_split_in"] == ["pipeline.py"]


def test_sklearn_capsule(sklearn_project):
    wr, parsed = _walk(sklearn_project)
    info = SklearnAdapter().extract(wr, parsed)
    section = SklearnAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "SKLEARN" in section
    assert "LogisticRegression" in section
    assert "train_test_split" in section
    assert "cross_val_score" in section


# ---------------- HuggingFace Datasets ----------------

@pytest.fixture
def datasets_project(tmp_path):
    (tmp_path / "load.py").write_text(
        "from datasets import load_dataset, Dataset, DatasetDict\n"
        "\n"
        "ds = load_dataset('imdb', split='train')\n"
        "ds2 = load_dataset('squad')\n"
        "from_pd = Dataset.from_pandas(None)\n"
        "from_csv = Dataset.from_csv('data.csv')\n"
        "combined = DatasetDict({'train': ds, 'val': ds2})\n"
        "ds = ds.map(lambda x: x)\n"
        "ds = ds.filter(lambda x: True)\n"
    )
    return tmp_path


def test_datasets_detect(datasets_project):
    wr, parsed = _walk(datasets_project)
    assert DatasetsHFAdapter.detect(wr, parsed) is True


def test_datasets_extract(datasets_project):
    wr, parsed = _walk(datasets_project)
    info = DatasetsHFAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    assert "dataset" in kinds
    assert "dataset_dict" in kinds
    assert "imdb" in info.meta["dataset_names"]
    assert "squad" in info.meta["dataset_names"]
    assert info.meta["map_in"] == ["load.py"]


def test_datasets_capsule(datasets_project):
    wr, parsed = _walk(datasets_project)
    info = DatasetsHFAdapter().extract(wr, parsed)
    section = DatasetsHFAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "DATASETS" in section
    assert "imdb" in section


# ---------------- Cross-cutting ----------------

@pytest.mark.parametrize("adapter_cls", [
    PyTorchAdapter, TransformersAdapter, SklearnAdapter, DatasetsHFAdapter,
])
def test_adapter_validate_class(adapter_cls):
    errors = adapter_cls.validate_class()
    assert errors == [], f"{adapter_cls.__name__}: {errors}"


@pytest.mark.parametrize("adapter_cls", [
    PyTorchAdapter, TransformersAdapter, SklearnAdapter, DatasetsHFAdapter,
])
def test_adapter_skips_unrelated_project(adapter_cls, tmp_path):
    (tmp_path / "x.py").write_text("def f(): pass\n")
    wr, parsed = _walk(tmp_path)
    assert adapter_cls.detect(wr, parsed) is False
    info = adapter_cls().extract(wr, parsed)
    assert info.entries == []
