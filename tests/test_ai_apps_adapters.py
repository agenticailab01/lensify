"""Tests for the _ai_apps adapter pack — LangChain, LlamaIndex, LangGraph,
Pydantic AI, DSPy."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "plugins" / "lensify" / "skills" / "lensify"
sys.path.insert(0, str(SCRIPTS))

from scripts.walker import walk  # noqa: E402
from scripts.ast_parser import parse_all  # noqa: E402
from scripts.frameworks._ai_apps.langchain import LangChainAdapter  # noqa: E402
from scripts.frameworks._ai_apps.llamaindex import LlamaIndexAdapter  # noqa: E402
from scripts.frameworks._ai_apps.langgraph import LangGraphAdapter  # noqa: E402
from scripts.frameworks._ai_apps.pydantic_ai import PydanticAIAdapter  # noqa: E402
from scripts.frameworks._ai_apps.dspy import DSPyAdapter  # noqa: E402


def _walk(p):
    wr = walk(str(p))
    return wr, parse_all(wr.code_files)


# ---------------- LangChain ----------------

@pytest.fixture
def langchain_project(tmp_path):
    (tmp_path / "rag.py").write_text(
        "from langchain_core.prompts import ChatPromptTemplate\n"
        "from langchain.chains import RetrievalQA\n"
        "from langchain.agents import AgentExecutor, create_react_agent\n"
        "from langchain.tools import tool\n"
        "\n"
        'qa_prompt = ChatPromptTemplate.from_template("answer {q}")\n'
        "qa_chain = RetrievalQA.from_chain_type(llm=None)\n"
        "react = create_react_agent(llm=None, tools=[], prompt=qa_prompt)\n"
        "agent = AgentExecutor(agent=react, tools=[])\n"
        "\n"
        "@tool\n"
        "def web_search(q: str) -> str:\n"
        '    """Search the web."""\n'
        "    return q\n"
        "\n"
        "rag_chain = qa_prompt | (lambda x: x) | (lambda y: y)\n"
    )
    return tmp_path


def test_langchain_detect(langchain_project):
    wr, parsed = _walk(langchain_project)
    assert LangChainAdapter.detect(wr, parsed) is True


def test_langchain_extract_finds_all_kinds(langchain_project):
    wr, parsed = _walk(langchain_project)
    info = LangChainAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    assert "prompt" in kinds
    assert "chain" in kinds
    assert "agent" in kinds
    assert "tool" in kinds


def test_langchain_capsule_section(langchain_project):
    wr, parsed = _walk(langchain_project)
    info = LangChainAdapter().extract(wr, parsed)
    section = LangChainAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "CHAINS" in section
    assert "qa_prompt" in section
    assert "web_search" in section


def test_langchain_detect_negative(tmp_path):
    (tmp_path / "x.py").write_text("import json\n")
    wr, parsed = _walk(tmp_path)
    assert LangChainAdapter.detect(wr, parsed) is False


# ---------------- LlamaIndex ----------------

@pytest.fixture
def llamaindex_project(tmp_path):
    (tmp_path / "rag.py").write_text(
        "from llama_index.core import VectorStoreIndex, Settings\n"
        "from llama_index.readers.file import SimpleDirectoryReader\n"
        "from llama_index.llms.openai import OpenAI\n"
        "\n"
        "Settings.llm = OpenAI(model='gpt-4')\n"
        "Settings.chunk_size = 512\n"
        "loader = SimpleDirectoryReader('./docs')\n"
        "docs = loader.load_data()\n"
        "index = VectorStoreIndex.from_documents(docs)\n"
        "qe = index.as_query_engine()\n"
        "chat = index.as_chat_engine()\n"
    )
    return tmp_path


def test_llamaindex_detect(llamaindex_project):
    wr, parsed = _walk(llamaindex_project)
    assert LlamaIndexAdapter.detect(wr, parsed) is True


def test_llamaindex_extract(llamaindex_project):
    wr, parsed = _walk(llamaindex_project)
    info = LlamaIndexAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    assert "index" in kinds
    assert "engine" in kinds
    assert "reader" in kinds
    assert "llm" in info.meta["settings"]
    assert "chunk_size" in info.meta["settings"]


def test_llamaindex_capsule(llamaindex_project):
    wr, parsed = _walk(llamaindex_project)
    info = LlamaIndexAdapter().extract(wr, parsed)
    section = LlamaIndexAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "LLAMA-INDEX" in section
    assert "VectorStoreIndex" in section


# ---------------- LangGraph ----------------

@pytest.fixture
def langgraph_project(tmp_path):
    (tmp_path / "agent.py").write_text(
        "from langgraph.graph import StateGraph\n"
        "from langgraph.checkpoint.memory import MemorySaver\n"
        "\n"
        "def classify(state): return state\n"
        "def search(state): return state\n"
        "def respond(state): return state\n"
        "\n"
        "workflow = StateGraph(dict)\n"
        "workflow.add_node('classify', classify)\n"
        "workflow.add_node('search', search)\n"
        "workflow.add_node('respond', respond)\n"
        "workflow.add_edge('classify', 'search')\n"
        "workflow.add_edge('search', 'respond')\n"
        "workflow.add_conditional_edges('classify', lambda s: 'search')\n"
        "workflow.set_entry_point('classify')\n"
        "workflow.set_finish_point('respond')\n"
        "memory = MemorySaver()\n"
        "app = workflow.compile(checkpointer=memory)\n"
    )
    return tmp_path


def test_langgraph_detect(langgraph_project):
    wr, parsed = _walk(langgraph_project)
    assert LangGraphAdapter.detect(wr, parsed) is True


def test_langgraph_extract(langgraph_project):
    wr, parsed = _walk(langgraph_project)
    info = LangGraphAdapter().extract(wr, parsed)
    assert len(info.entries) == 1
    e = info.entries[0]
    assert e.kind == "graph"
    assert e.name == "workflow"
    assert set(e.meta["nodes"]) == {"classify", "search", "respond"}
    assert ("classify", "search") in e.meta["edges"]
    assert e.meta["entry"] == "classify"
    assert e.meta["finish"] == "respond"
    assert e.meta["checkpointer"] == "MemorySaver"


def test_langgraph_capsule(langgraph_project):
    wr, parsed = _walk(langgraph_project)
    info = LangGraphAdapter().extract(wr, parsed)
    section = LangGraphAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "LANGGRAPH" in section
    assert "workflow" in section
    assert "classify→search" in section


# ---------------- Pydantic AI ----------------

@pytest.fixture
def pydantic_ai_project(tmp_path):
    (tmp_path / "bot.py").write_text(
        "from pydantic_ai import Agent\n"
        "\n"
        "support_agent = Agent('openai:gpt-4o', deps_type=str)\n"
        "\n"
        "@support_agent.system_prompt\n"
        "async def sys_prompt(ctx) -> str:\n"
        "    return 'helpful'\n"
        "\n"
        "@support_agent.tool\n"
        "async def lookup_order(ctx, order_id: str) -> dict:\n"
        "    return {'id': order_id}\n"
        "\n"
        "@support_agent.tool_plain\n"
        "def send_email(to: str, body: str) -> bool:\n"
        "    return True\n"
        "\n"
        "@support_agent.result_validator\n"
        "async def validate(ctx, result):\n"
        "    return result\n"
    )
    return tmp_path


def test_pydantic_ai_detect(pydantic_ai_project):
    wr, parsed = _walk(pydantic_ai_project)
    assert PydanticAIAdapter.detect(wr, parsed) is True


def test_pydantic_ai_extract(pydantic_ai_project):
    wr, parsed = _walk(pydantic_ai_project)
    info = PydanticAIAdapter().extract(wr, parsed)
    assert len(info.entries) == 1
    e = info.entries[0]
    assert e.kind == "agent"
    assert e.name == "support_agent"
    assert "lookup_order" in e.meta["tools"]
    assert "send_email" in e.meta["tools"]
    assert e.meta["has_sysprompt"] is True
    assert e.meta["has_validator"] is True
    assert "gpt-4o" in e.meta["model"]


def test_pydantic_ai_capsule(pydantic_ai_project):
    wr, parsed = _walk(pydantic_ai_project)
    info = PydanticAIAdapter().extract(wr, parsed)
    section = PydanticAIAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "PYDANTIC-AI" in section
    assert "support_agent" in section
    assert "system_prompt" in section


# ---------------- DSPy ----------------

@pytest.fixture
def dspy_project(tmp_path):
    (tmp_path / "program.py").write_text(
        "import dspy\n"
        "\n"
        "class BasicQA(dspy.Signature):\n"
        "    question = dspy.InputField()\n"
        "    answer = dspy.OutputField()\n"
        "\n"
        "class RAGPipeline(dspy.Module):\n"
        "    def __init__(self):\n"
        "        self.qa = dspy.ChainOfThought(BasicQA)\n"
        "    def forward(self, q): return self.qa(question=q)\n"
        "\n"
        "qa = dspy.Predict(BasicQA)\n"
        "react = dspy.ReAct(BasicQA, tools=[])\n"
        "optimizer = dspy.BootstrapFewShot(metric=lambda x, y: True)\n"
        "dspy.settings.configure(lm=None)\n"
    )
    return tmp_path


def test_dspy_detect(dspy_project):
    wr, parsed = _walk(dspy_project)
    assert DSPyAdapter.detect(wr, parsed) is True


def test_dspy_extract(dspy_project):
    wr, parsed = _walk(dspy_project)
    info = DSPyAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    assert "signature" in kinds
    assert "module" in kinds
    assert "predictor" in kinds
    assert "optimizer" in kinds
    assert info.meta["configured"] is True


def test_dspy_capsule(dspy_project):
    wr, parsed = _walk(dspy_project)
    info = DSPyAdapter().extract(wr, parsed)
    section = DSPyAdapter().capsule_section(info, budget_tokens=500)
    assert section is not None
    assert "DSPY" in section
    assert "BasicQA" in section
    assert "ChainOfThought" in section
    assert "settings.configure" in section


# ---------------- Cross-cutting ----------------

@pytest.mark.parametrize("adapter_cls", [
    LangChainAdapter, LlamaIndexAdapter, LangGraphAdapter,
    PydanticAIAdapter, DSPyAdapter,
])
def test_adapter_validate_class(adapter_cls):
    """Every _ai_apps adapter passes the base class self-check."""
    errors = adapter_cls.validate_class()
    assert errors == [], f"{adapter_cls.__name__}: {errors}"


@pytest.mark.parametrize("adapter_cls", [
    LangChainAdapter, LlamaIndexAdapter, LangGraphAdapter,
    PydanticAIAdapter, DSPyAdapter,
])
def test_adapter_skips_unrelated_project(adapter_cls, tmp_path):
    """An empty project (no relevant imports) must yield no entries."""
    (tmp_path / "x.py").write_text("def f(): pass\n")
    wr, parsed = _walk(tmp_path)
    assert adapter_cls.detect(wr, parsed) is False
    info = adapter_cls().extract(wr, parsed)
    assert info.entries == []
