"""Tests for the _experiment adapter pack — Weights & Biases, MLflow, Comet."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "lensify"
sys.path.insert(0, str(SCRIPTS))

from scripts.walker import walk  # noqa: E402
from scripts.ast_parser import parse_all  # noqa: E402
from scripts.frameworks._experiment.wandb import WandbAdapter  # noqa: E402
from scripts.frameworks._experiment.mlflow import MLflowAdapter  # noqa: E402
from scripts.frameworks._experiment.comet import CometAdapter  # noqa: E402


def _walk(p):
    wr = walk(str(p))
    return wr, parse_all(wr.code_files)


# ---------------- Weights & Biases ----------------

@pytest.fixture
def wandb_project(tmp_path):
    (tmp_path / "train.py").write_text(
        "import wandb\n"
        "\n"
        "run = wandb.init(\n"
        "    project='llm-finetune', entity='acme-ai',\n"
        "    name='exp-001', config={'lr': 1e-4},\n"
        ")\n"
        "\n"
        "wandb.watch(None, log='all')\n"
        "\n"
        "model_art = wandb.Artifact(name='best_model', type='model')\n"
        "data_art = wandb.Artifact('train_set', type='dataset')\n"
        "\n"
        "for step in range(3):\n"
        "    wandb.log({'loss': 0.5, 'step': step})\n"
        "wandb.log({'final_acc': 0.95})\n"
        "wandb.log_artifact(model_art)\n"
        "\n"
        "sweep_id = wandb.sweep({'method': 'random'})\n"
        "wandb.agent(sweep_id, lambda: None, count=5)\n"
    )
    return tmp_path


def test_wandb_detect(wandb_project):
    wr, parsed = _walk(wandb_project)
    assert WandbAdapter.detect(wr, parsed) is True


def test_wandb_extract(wandb_project):
    wr, parsed = _walk(wandb_project)
    info = WandbAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    assert "run" in kinds
    assert "artifact" in kinds
    assert "llm-finetune" in info.meta["projects"]
    assert "acme-ai" in info.meta["entities"]
    # Static regex counts source-line occurrences, not runtime calls — so
    # the for-loop's wandb.log counts as 1 even though it executes 3 times.
    assert info.meta["ops"]["log"] == 2
    assert info.meta["ops"]["log_artifact"] == 1
    assert info.meta["ops"]["sweep_or_agent"] == 2
    assert info.meta["ops"]["watch"] == 1


def test_wandb_capsule(wandb_project):
    wr, parsed = _walk(wandb_project)
    info = WandbAdapter().extract(wr, parsed)
    section = WandbAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "WANDB" in section
    assert "llm-finetune" in section
    assert "best_model" in section
    assert "log×2" in section


# ---------------- MLflow ----------------

@pytest.fixture
def mlflow_project(tmp_path):
    (tmp_path / "train.py").write_text(
        "import mlflow\n"
        "import mlflow.sklearn\n"
        "import mlflow.pytorch\n"
        "\n"
        "mlflow.set_tracking_uri('http://mlflow.example.com:5000')\n"
        "mlflow.set_experiment('demand-forecast')\n"
        "\n"
        "with mlflow.start_run(run_name='baseline-v2', nested=False):\n"
        "    mlflow.log_param('lr', 0.01)\n"
        "    mlflow.log_param('epochs', 100)\n"
        "    mlflow.log_metric('rmse', 0.15)\n"
        "    mlflow.log_metric('mae', 0.10)\n"
        "    mlflow.log_artifact('plot.png')\n"
        "    mlflow.sklearn.log_model(None, 'baseline_rf')\n"
        "\n"
        "with mlflow.start_run(run_name='dl-attempt'):\n"
        "    mlflow.pytorch.log_model(None, 'transformer_v1')\n"
    )
    return tmp_path


def test_mlflow_detect(mlflow_project):
    wr, parsed = _walk(mlflow_project)
    assert MLflowAdapter.detect(wr, parsed) is True


def test_mlflow_extract(mlflow_project):
    wr, parsed = _walk(mlflow_project)
    info = MLflowAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    assert "experiment" in kinds
    assert "run" in kinds
    assert "model" in kinds
    assert "demand-forecast" in info.meta["experiments"]
    assert "http://mlflow.example.com:5000" in info.meta["tracking_uris"]
    assert "sklearn" in info.meta["model_flavors"]
    assert "pytorch" in info.meta["model_flavors"]
    assert info.meta["ops"]["log_param"] == 2
    assert info.meta["ops"]["log_metric"] == 2
    assert info.meta["ops"]["log_artifact"] == 1


def test_mlflow_capsule(mlflow_project):
    wr, parsed = _walk(mlflow_project)
    info = MLflowAdapter().extract(wr, parsed)
    section = MLflowAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "MLFLOW" in section
    assert "demand-forecast" in section
    assert "sklearn" in section
    assert "pytorch" in section


# ---------------- Comet ----------------

@pytest.fixture
def comet_project(tmp_path):
    (tmp_path / "train.py").write_text(
        "from comet_ml import Experiment, OfflineExperiment, ExistingExperiment\n"
        "\n"
        "exp = Experiment(\n"
        "    api_key='xxx', project_name='rag-eval', workspace='acme-ai',\n"
        ")\n"
        "offline_exp = OfflineExperiment(\n"
        "    project_name='offline-eval', workspace='acme-ai',\n"
        "    offline_directory='./logs',\n"
        ")\n"
        "resumed = ExistingExperiment(api_key='xxx', previous_experiment='abc123')\n"
        "\n"
        "exp.log_parameter('lr', 0.001)\n"
        "exp.log_parameters({'a': 1, 'b': 2})\n"
        "exp.log_metric('acc', 0.92)\n"
        "exp.log_metric('f1', 0.88)\n"
        "exp.log_asset('plot.png')\n"
        "exp.log_model('best', 'model.pkl')\n"
    )
    return tmp_path


def test_comet_detect(comet_project):
    wr, parsed = _walk(comet_project)
    assert CometAdapter.detect(wr, parsed) is True


def test_comet_extract(comet_project):
    wr, parsed = _walk(comet_project)
    info = CometAdapter().extract(wr, parsed)
    classes = {e.meta["class"] for e in info.entries}
    names = {e.name for e in info.entries}
    assert "Experiment" in classes
    assert "OfflineExperiment" in classes
    assert "ExistingExperiment" in classes
    assert "exp" in names
    assert "offline_exp" in names
    assert "rag-eval" in info.meta["projects"]
    assert "offline-eval" in info.meta["projects"]
    assert "acme-ai" in info.meta["workspaces"]
    assert info.meta["log_counts"]["log_metric"] == 2
    assert info.meta["log_counts"]["log_parameter"] == 1
    assert info.meta["log_counts"]["log_parameters"] == 1


def test_comet_capsule(comet_project):
    wr, parsed = _walk(comet_project)
    info = CometAdapter().extract(wr, parsed)
    section = CometAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "COMET" in section
    assert "rag-eval" in section
    assert "acme-ai" in section
    assert "log_metric×2" in section


# ---------------- Cross-cutting ----------------

@pytest.mark.parametrize("adapter_cls", [
    WandbAdapter, MLflowAdapter, CometAdapter,
])
def test_adapter_validate_class(adapter_cls):
    errors = adapter_cls.validate_class()
    assert errors == [], f"{adapter_cls.__name__}: {errors}"


@pytest.mark.parametrize("adapter_cls", [
    WandbAdapter, MLflowAdapter, CometAdapter,
])
def test_adapter_skips_unrelated_project(adapter_cls, tmp_path):
    (tmp_path / "x.py").write_text("def f(): pass\n")
    wr, parsed = _walk(tmp_path)
    assert adapter_cls.detect(wr, parsed) is False
    info = adapter_cls().extract(wr, parsed)
    assert info.entries == []
