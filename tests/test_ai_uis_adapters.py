"""Tests for the _ai_uis adapter pack — Streamlit, Gradio, Chainlit."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "plugins" / "lensify" / "skills" / "lensify"
sys.path.insert(0, str(SCRIPTS))

from scripts.walker import walk  # noqa: E402
from scripts.ast_parser import parse_all  # noqa: E402
from scripts.frameworks._ai_uis.streamlit import StreamlitAdapter  # noqa: E402
from scripts.frameworks._ai_uis.gradio import GradioAdapter  # noqa: E402
from scripts.frameworks._ai_uis.chainlit import ChainlitAdapter  # noqa: E402


def _walk(p):
    wr = walk(str(p))
    return wr, parse_all(wr.code_files)


# ---------------- Streamlit ----------------

@pytest.fixture
def streamlit_project(tmp_path):
    (tmp_path / "app.py").write_text(
        "import streamlit as st\n"
        "\n"
        "st.set_page_config(page_title='Demo', layout='wide')\n"
        "\n"
        "@st.cache_data\n"
        "def load_users():\n"
        "    return []\n"
        "\n"
        "@st.cache_resource\n"
        "def get_model():\n"
        "    return None\n"
        "\n"
        "st.title('Hello')\n"
        "name = st.text_input('Your name')\n"
        "age = st.slider('Age', 0, 100)\n"
        "if st.button('Greet'):\n"
        "    st.write(f'Hi {name}')\n"
        "\n"
        "with st.form('signup'):\n"
        "    email = st.text_input('Email')\n"
        "    st.form_submit_button('Submit')\n"
        "\n"
        "st.session_state['count'] = st.session_state.get('count', 0) + 1\n"
        "msg = st.chat_input('Ask me anything')\n"
    )
    (tmp_path / "pages").mkdir()
    (tmp_path / "pages" / "settings.py").write_text(
        "import streamlit as st\n"
        "st.title('Settings')\n"
        "st.selectbox('Theme', ['dark', 'light'])\n"
        "st.checkbox('Enable beta')\n"
    )
    return tmp_path


def test_streamlit_detect(streamlit_project):
    wr, parsed = _walk(streamlit_project)
    assert StreamlitAdapter.detect(wr, parsed) is True


def test_streamlit_extract(streamlit_project):
    wr, parsed = _walk(streamlit_project)
    info = StreamlitAdapter().extract(wr, parsed)
    paths = {e.path for e in info.entries}
    assert "app.py" in paths
    assert "pages/settings.py" in paths
    # Find the home page
    home = next(e for e in info.entries if e.path == "app.py")
    assert home.meta["has_page_config"] is True
    assert home.meta["uses_session_state"] is True
    assert "text_input" in home.meta["widgets"]
    assert "slider" in home.meta["widgets"]
    assert "chat_input" in home.meta["widgets"]
    assert home.meta["forms"]
    # Cache functions tracked separately
    cached_names = {c[0] for c in info.meta["cached_fns"]}
    assert "load_users" in cached_names
    assert "get_model" in cached_names


def test_streamlit_capsule(streamlit_project):
    wr, parsed = _walk(streamlit_project)
    info = StreamlitAdapter().extract(wr, parsed)
    section = StreamlitAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "STREAMLIT" in section
    assert "page `app`" in section
    assert "session_state" in section
    assert "load_users" in section


# ---------------- Gradio ----------------

@pytest.fixture
def gradio_project(tmp_path):
    (tmp_path / "app.py").write_text(
        "import gradio as gr\n"
        "\n"
        "def classify(text): return text\n"
        "def greet(name): return f'Hi {name}'\n"
        "\n"
        "sentiment_ui = gr.Interface(\n"
        "    fn=classify, inputs=gr.Textbox(), outputs=gr.Label(),\n"
        "    title='Sentiment Demo',\n"
        ")\n"
        "\n"
        "with gr.Blocks(title='Multi-tab') as demo:\n"
        "    name = gr.Textbox()\n"
        "    out = gr.Textbox()\n"
        "    btn = gr.Button('Greet')\n"
        "    btn.click(greet, [name], [out])\n"
        "\n"
        "chat = gr.ChatInterface(fn=lambda m, h: m, title='Chat')\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    demo.launch(server_port=7860)\n"
    )
    return tmp_path


def test_gradio_detect(gradio_project):
    wr, parsed = _walk(gradio_project)
    assert GradioAdapter.detect(wr, parsed) is True


def test_gradio_extract(gradio_project):
    wr, parsed = _walk(gradio_project)
    info = GradioAdapter().extract(wr, parsed)
    classes = {e.meta.get("class") for e in info.entries}
    titles = {e.meta.get("title") for e in info.entries}
    assert "Interface" in classes
    assert "Blocks" in classes
    assert "ChatInterface" in classes
    assert "Sentiment Demo" in titles
    assert "Multi-tab" in titles
    assert "Textbox" in info.meta["components"]
    assert "Button" in info.meta["components"]
    assert info.meta["launches"]
    assert info.meta["launches"][0][0] == "demo"


def test_gradio_capsule(gradio_project):
    wr, parsed = _walk(gradio_project)
    info = GradioAdapter().extract(wr, parsed)
    section = GradioAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "GRADIO" in section
    assert "Sentiment Demo" in section
    assert "components:" in section
    assert ".launch()" in section


# ---------------- Chainlit ----------------

@pytest.fixture
def chainlit_project(tmp_path):
    (tmp_path / "app.py").write_text(
        "import chainlit as cl\n"
        "\n"
        "@cl.on_chat_start\n"
        "async def start():\n"
        "    await cl.Message(content='Welcome!').send()\n"
        "\n"
        "@cl.on_message\n"
        "async def main(msg: cl.Message):\n"
        "    step = cl.Step(name='thinking')\n"
        "    await cl.Message(content=msg.content).send()\n"
        "\n"
        "@cl.action_callback('rerun')\n"
        "async def rerun_action(action: cl.Action):\n"
        "    await cl.Message(content='re-running').send()\n"
        "\n"
        "@cl.on_settings_update\n"
        "async def settings(s):\n"
        "    pass\n"
    )
    return tmp_path


def test_chainlit_detect(chainlit_project):
    wr, parsed = _walk(chainlit_project)
    assert ChainlitAdapter.detect(wr, parsed) is True


def test_chainlit_extract(chainlit_project):
    wr, parsed = _walk(chainlit_project)
    info = ChainlitAdapter().extract(wr, parsed)
    events = {e.meta["event"] for e in info.entries}
    names = {e.name for e in info.entries}
    assert "on_chat_start" in events
    assert "on_message" in events
    assert "action_callback" in events
    assert "on_settings_update" in events
    assert "start" in names
    assert "main" in names
    assert "Message" in info.meta["ui_primitives"]
    assert "Step" in info.meta["ui_primitives"]


def test_chainlit_capsule(chainlit_project):
    wr, parsed = _walk(chainlit_project)
    info = ChainlitAdapter().extract(wr, parsed)
    section = ChainlitAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "CHAINLIT" in section
    assert "on_message" in section
    assert "UI primitives:" in section


# ---------------- Cross-cutting ----------------

@pytest.mark.parametrize("adapter_cls", [
    StreamlitAdapter, GradioAdapter, ChainlitAdapter,
])
def test_adapter_validate_class(adapter_cls):
    errors = adapter_cls.validate_class()
    assert errors == [], f"{adapter_cls.__name__}: {errors}"


@pytest.mark.parametrize("adapter_cls", [
    StreamlitAdapter, GradioAdapter, ChainlitAdapter,
])
def test_adapter_skips_unrelated_project(adapter_cls, tmp_path):
    (tmp_path / "x.py").write_text("def f(): pass\n")
    wr, parsed = _walk(tmp_path)
    assert adapter_cls.detect(wr, parsed) is False
    info = adapter_cls().extract(wr, parsed)
    assert info.entries == []
