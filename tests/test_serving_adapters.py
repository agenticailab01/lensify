"""Tests for the _serving adapter pack — vLLM, Triton, BentoML, Ray Serve."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "lensify"
sys.path.insert(0, str(SCRIPTS))

from scripts.walker import walk  # noqa: E402
from scripts.ast_parser import parse_all  # noqa: E402
from scripts.frameworks._serving.vllm import VLLMAdapter  # noqa: E402
from scripts.frameworks._serving.triton import TritonAdapter  # noqa: E402
from scripts.frameworks._serving.bentoml import BentoMLAdapter  # noqa: E402
from scripts.frameworks._serving.ray_serve import RayServeAdapter  # noqa: E402


def _walk(p):
    wr = walk(str(p))
    return wr, parse_all(wr.code_files)


# ---------------- vLLM ----------------

@pytest.fixture
def vllm_project(tmp_path):
    (tmp_path / "serve.py").write_text(
        "from vllm import LLM, SamplingParams\n"
        "from vllm.engine.async_llm_engine import AsyncLLMEngine\n"
        "from vllm.entrypoints.openai import api_server\n"
        "\n"
        "engine = LLM(model='meta-llama/Llama-3-8b-Instruct', tensor_parallel_size=2)\n"
        "params = SamplingParams(temperature=0.7, max_tokens=512)\n"
        "async_engine = AsyncLLMEngine.from_engine_args(None)\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    api_server.run_server(host='0.0.0.0', port=8000)\n"
    )
    return tmp_path


def test_vllm_detect(vllm_project):
    wr, parsed = _walk(vllm_project)
    assert VLLMAdapter.detect(wr, parsed) is True


def test_vllm_extract(vllm_project):
    wr, parsed = _walk(vllm_project)
    info = VLLMAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    assert "engine" in kinds
    assert "sampling" in kinds
    assert "meta-llama/Llama-3-8b-Instruct" in info.meta["checkpoints"]
    assert info.meta["server_files"] == ["serve.py"]


def test_vllm_capsule(vllm_project):
    wr, parsed = _walk(vllm_project)
    info = VLLMAdapter().extract(wr, parsed)
    section = VLLMAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "VLLM" in section
    assert "Llama-3-8b-Instruct" in section
    assert "OpenAI-compatible" in section


# ---------------- Triton ----------------

@pytest.fixture
def triton_project(tmp_path):
    (tmp_path / "client.py").write_text(
        "import tritonclient.http as httpclient\n"
        "from tritonclient.grpc import InferenceServerClient, InferInput, InferRequestedOutput\n"
        "\n"
        "client = httpclient.InferenceServerClient(url='localhost:8000')\n"
        "grpc_client = InferenceServerClient(url='localhost:8001')\n"
        "\n"
        "in_ids = InferInput('input_ids', [1, 128], 'INT32')\n"
        "in_mask = InferInput('attention_mask', [1, 128], 'INT32')\n"
        "out_logits = InferRequestedOutput('logits')\n"
        "\n"
        "result = client.infer(model_name='bert_classifier', inputs=[in_ids, in_mask])\n"
        "client.infer('embedder', inputs=[in_ids])\n"
    )
    return tmp_path


def test_triton_detect(triton_project):
    wr, parsed = _walk(triton_project)
    assert TritonAdapter.detect(wr, parsed) is True


def test_triton_extract(triton_project):
    wr, parsed = _walk(triton_project)
    info = TritonAdapter().extract(wr, parsed)
    client_names = {e.name for e in info.entries}
    assert "client" in client_names
    assert "grpc_client" in client_names
    assert "bert_classifier" in info.meta["models_referenced"]
    assert "embedder" in info.meta["models_referenced"]
    assert "input_ids" in info.meta["inputs"]
    assert "logits" in info.meta["outputs"]


def test_triton_capsule(triton_project):
    wr, parsed = _walk(triton_project)
    info = TritonAdapter().extract(wr, parsed)
    section = TritonAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "TRITON" in section
    assert "bert_classifier" in section


# ---------------- BentoML ----------------

@pytest.fixture
def bentoml_project(tmp_path):
    (tmp_path / "service.py").write_text(
        "import bentoml\n"
        "from bentoml.io import NumpyNdarray, JSON, Text\n"
        "\n"
        "summarizer_runner = bentoml.Runner(None, name='summarizer')\n"
        "input_spec = NumpyNdarray()\n"
        "output_spec = NumpyNdarray()\n"
        "raw_spec = bentoml.io.JSON()\n"
        "\n"
        "@bentoml.service(resources={'cpu': '2'})\n"
        "class SummaryService:\n"
        "    @bentoml.api\n"
        "    async def summarize(self, text: str) -> str:\n"
        "        return text\n"
        "\n"
        "    @bentoml.task\n"
        "    def long_job(self, payload: dict) -> dict:\n"
        "        return payload\n"
        "\n"
        "    @bentoml.async_task\n"
        "    async def streaming_job(self, q: str) -> str:\n"
        "        return q\n"
    )
    return tmp_path


def test_bentoml_detect(bentoml_project):
    wr, parsed = _walk(bentoml_project)
    assert BentoMLAdapter.detect(wr, parsed) is True


def test_bentoml_extract(bentoml_project):
    wr, parsed = _walk(bentoml_project)
    info = BentoMLAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    names = {e.name for e in info.entries}
    assert "service" in kinds
    assert "endpoint" in kinds
    assert "runner" in kinds
    assert "SummaryService" in names
    assert "summarize" in names
    assert "long_job" in names
    assert "streaming_job" in names
    assert "NumpyNdarray" in info.meta["io_types"]


def test_bentoml_capsule(bentoml_project):
    wr, parsed = _walk(bentoml_project)
    info = BentoMLAdapter().extract(wr, parsed)
    section = BentoMLAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "BENTOML" in section
    assert "SummaryService" in section
    assert "I/O schemas" in section


# ---------------- Ray Serve ----------------

@pytest.fixture
def ray_serve_project(tmp_path):
    (tmp_path / "app.py").write_text(
        "from ray import serve\n"
        "from fastapi import FastAPI\n"
        "\n"
        "fastapi_app = FastAPI()\n"
        "\n"
        "@serve.deployment(num_replicas=2)\n"
        "@serve.ingress(fastapi_app)\n"
        "class TextService:\n"
        "    def __init__(self): pass\n"
        "\n"
        "@serve.deployment\n"
        "def helper():\n"
        "    return 'ok'\n"
        "\n"
        "app = TextService.bind()\n"
        "h = helper.bind()\n"
        "serve.run(app, route_prefix='/text')\n"
    )
    return tmp_path


def test_ray_serve_detect(ray_serve_project):
    wr, parsed = _walk(ray_serve_project)
    assert RayServeAdapter.detect(wr, parsed) is True


def test_ray_serve_extract(ray_serve_project):
    wr, parsed = _walk(ray_serve_project)
    info = RayServeAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    names = {e.name for e in info.entries}
    assert "deployment" in kinds
    assert "ingress" in kinds
    assert "binding" in kinds
    assert "TextService" in names
    assert "helper" in names
    assert info.meta["run_files"] == ["app.py"]


def test_ray_serve_capsule(ray_serve_project):
    wr, parsed = _walk(ray_serve_project)
    info = RayServeAdapter().extract(wr, parsed)
    section = RayServeAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "RAY-SERVE" in section
    assert "TextService" in section
    assert "serve.run()" in section


def test_ray_serve_quiet_on_ray_without_serve(tmp_path):
    """Ray Train / Tune / Data projects must NOT emit a Ray-Serve section."""
    (tmp_path / "train.py").write_text(
        "import ray\n"
        "from ray import train\n"
        "ray.init()\n"
        "def trainer(): pass\n"
        "train.run(trainer)\n"
    )
    wr, parsed = _walk(tmp_path)
    # detect() still fires (broad signature) — but extract() yields nothing
    assert RayServeAdapter.detect(wr, parsed) is True
    info = RayServeAdapter().extract(wr, parsed)
    assert info.entries == []
    assert info.meta["run_files"] == []


# ---------------- Cross-cutting ----------------

@pytest.mark.parametrize("adapter_cls", [
    VLLMAdapter, TritonAdapter, BentoMLAdapter, RayServeAdapter,
])
def test_adapter_validate_class(adapter_cls):
    errors = adapter_cls.validate_class()
    assert errors == [], f"{adapter_cls.__name__}: {errors}"


@pytest.mark.parametrize("adapter_cls", [
    VLLMAdapter, TritonAdapter, BentoMLAdapter, RayServeAdapter,
])
def test_adapter_skips_unrelated_project(adapter_cls, tmp_path):
    (tmp_path / "x.py").write_text("def f(): pass\n")
    wr, parsed = _walk(tmp_path)
    assert adapter_cls.detect(wr, parsed) is False
    info = adapter_cls().extract(wr, parsed)
    assert info.entries == []
