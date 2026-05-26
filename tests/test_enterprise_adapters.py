"""Tests for the expanded _enterprise pack — SQLAlchemy, Pydantic, Vue,
Tailwind, Docker Compose.

(The FastAPI adapter is covered separately in test_fastapi_adapter.py.)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "plugins" / "lensify" / "skills" / "lensify"
sys.path.insert(0, str(SCRIPTS))

from scripts.walker import walk  # noqa: E402
from scripts.ast_parser import parse_all  # noqa: E402
from scripts.frameworks._enterprise.sqlalchemy import SQLAlchemyAdapter  # noqa: E402
from scripts.frameworks._enterprise.pydantic import PydanticAdapter  # noqa: E402
from scripts.frameworks._enterprise.vue import VueAdapter  # noqa: E402
from scripts.frameworks._enterprise.tailwind import TailwindAdapter  # noqa: E402
from scripts.frameworks._enterprise.docker_compose import DockerComposeAdapter  # noqa: E402


def _walk(p):
    wr = walk(str(p))
    return wr, parse_all(wr.code_files)


# ---------------- SQLAlchemy ----------------

@pytest.fixture
def sqlalchemy_project(tmp_path):
    (tmp_path / "models.py").write_text(
        "from sqlalchemy import Column, Integer, String, ForeignKey, create_engine\n"
        "from sqlalchemy.orm import declarative_base, relationship, sessionmaker\n"
        "\n"
        "Base = declarative_base()\n"
        "\n"
        "class User(Base):\n"
        "    __tablename__ = 'users'\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    email = Column(String)\n"
        "    name = Column(String)\n"
        "    posts = relationship('Post', back_populates='author')\n"
        "\n"
        "class Post(Base):\n"
        "    __tablename__ = 'posts'\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    user_id = Column(Integer, ForeignKey('users.id'))\n"
        "    title = Column(String)\n"
        "    author = relationship('User', back_populates='posts')\n"
        "\n"
        "engine = create_engine('postgresql://user:pass@localhost/db')\n"
        "SessionLocal = sessionmaker(bind=engine)\n"
    )
    return tmp_path


def test_sqlalchemy_detect(sqlalchemy_project):
    wr, parsed = _walk(sqlalchemy_project)
    assert SQLAlchemyAdapter.detect(wr, parsed) is True


def test_sqlalchemy_extract(sqlalchemy_project):
    wr, parsed = _walk(sqlalchemy_project)
    info = SQLAlchemyAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    names = {e.name for e in info.entries}
    assert "model" in kinds
    assert "engine" in kinds
    assert "session" in kinds
    assert "User" in names
    assert "Post" in names
    assert "users" in info.meta["tables"]
    assert "posts" in info.meta["tables"]
    # Password redaction
    engine_entry = next(e for e in info.entries if e.kind == "engine")
    assert "pass" not in engine_entry.meta["url"]
    assert "***" in engine_entry.meta["url"]


def test_sqlalchemy_capsule(sqlalchemy_project):
    wr, parsed = _walk(sqlalchemy_project)
    info = SQLAlchemyAdapter().extract(wr, parsed)
    section = SQLAlchemyAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "SQLALCHEMY" in section
    assert "User" in section
    assert "table users" in section
    assert "relationships" in section


# ---------------- Pydantic ----------------

@pytest.fixture
def pydantic_project(tmp_path):
    (tmp_path / "schemas.py").write_text(
        "from pydantic import BaseModel, Field, field_validator, ConfigDict\n"
        "\n"
        "class UserIn(BaseModel):\n"
        "    name: str\n"
        "    email: str = Field(..., min_length=3)\n"
        "    age: int = Field(default=0, ge=0)\n"
        "\n"
        "    @field_validator('email')\n"
        "    def check_email(cls, v): return v\n"
        "\n"
        "class UserOut(BaseModel):\n"
        "    model_config = ConfigDict(from_attributes=True)\n"
        "    id: int\n"
        "    name: str\n"
        "    email: str\n"
        "    is_active: bool = True\n"
        "\n"
        "class Token(BaseModel):\n"
        "    access_token: str\n"
        "    token_type: str = 'bearer'\n"
    )
    return tmp_path


def test_pydantic_detect(pydantic_project):
    wr, parsed = _walk(pydantic_project)
    assert PydanticAdapter.detect(wr, parsed) is True


def test_pydantic_extract(pydantic_project):
    wr, parsed = _walk(pydantic_project)
    info = PydanticAdapter().extract(wr, parsed)
    names = {e.name for e in info.entries}
    assert "UserIn" in names
    assert "UserOut" in names
    assert "Token" in names
    user_in = next(e for e in info.entries if e.name == "UserIn")
    assert user_in.meta["fields"] >= 3
    user_out = next(e for e in info.entries if e.name == "UserOut")
    assert user_out.meta["has_config"] is True
    assert info.meta["validators"]["field_validator"] == 1


def test_pydantic_capsule(pydantic_project):
    wr, parsed = _walk(pydantic_project)
    info = PydanticAdapter().extract(wr, parsed)
    section = PydanticAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "PYDANTIC" in section
    assert "UserIn" in section
    assert "fields" in section
    assert "field_validator" in section


# ---------------- Vue SFC ----------------

@pytest.fixture
def vue_project(tmp_path):
    (tmp_path / "App.vue").write_text(
        "<template>\n"
        "  <div>{{ greeting }}</div>\n"
        "</template>\n"
        "<script setup lang='ts'>\n"
        "import { ref, computed } from 'vue'\n"
        "import { useRoute } from 'vue-router'\n"
        "\n"
        "const props = defineProps<{ name: string; age: number }>()\n"
        "const emit = defineEmits(['save', 'cancel'])\n"
        "\n"
        "const route = useRoute()\n"
        "const greeting = computed(() => `Hello ${props.name}`)\n"
        "defineExpose({ greeting })\n"
        "</script>\n"
    )
    (tmp_path / "Legacy.vue").write_text(
        "<template><button @click=\"$emit('click')\">x</button></template>\n"
        "<script>\n"
        "export default {\n"
        "  props: { label: String, disabled: Boolean },\n"
        "  emits: ['click', 'hover'],\n"
        "}\n"
        "</script>\n"
    )
    return tmp_path


def test_vue_detect(vue_project):
    wr, parsed = _walk(vue_project)
    assert VueAdapter.detect(wr, parsed) is True


def test_vue_extract(vue_project):
    wr, parsed = _walk(vue_project)
    info = VueAdapter().extract(wr, parsed)
    names = {e.name for e in info.entries}
    assert "App" in names
    assert "Legacy" in names
    app = next(e for e in info.entries if e.name == "App")
    assert app.meta["api_style"] == "setup"
    assert "save" in app.meta["emits"]
    assert "cancel" in app.meta["emits"]
    assert "useRoute" in app.meta["composables"]
    assert app.meta["exposes"] is True
    legacy = next(e for e in info.entries if e.name == "Legacy")
    assert legacy.meta["api_style"] == "options"
    assert "label" in legacy.meta["props"]


def test_vue_capsule(vue_project):
    wr, parsed = _walk(vue_project)
    info = VueAdapter().extract(wr, parsed)
    section = VueAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "VUE" in section
    assert "App" in section
    assert "api=setup" in section


# ---------------- Tailwind ----------------

@pytest.fixture
def tailwind_project(tmp_path):
    (tmp_path / "tailwind.config.js").write_text(
        "/** @type {import('tailwindcss').Config} */\n"
        "module.exports = {\n"
        "  content: ['./src/**/*.{vue,ts}', './index.html'],\n"
        "  theme: {\n"
        "    extend: {\n"
        "      colors: { brand: '#0066cc', accent: '#ff9900', subtle: '#888' },\n"
        "      fontFamily: { sans: ['Inter'], display: ['Cal'] },\n"
        "      spacing: { '128': '32rem' },\n"
        "    },\n"
        "  },\n"
        "  plugins: [require('@tailwindcss/forms'), require('@tailwindcss/typography')],\n"
        "}\n"
    )
    return tmp_path


def test_tailwind_detect(tailwind_project):
    wr, parsed = _walk(tailwind_project)
    assert TailwindAdapter.detect(wr, parsed) is True


def test_tailwind_extract(tailwind_project):
    wr, parsed = _walk(tailwind_project)
    info = TailwindAdapter().extract(wr, parsed)
    assert len(info.entries) == 1
    e = info.entries[0]
    assert "brand" in e.meta["custom_colors"]
    assert "accent" in e.meta["custom_colors"]
    assert "sans" in e.meta["custom_fonts"]
    assert e.meta["has_spacing_extension"] is True
    plugins = e.meta["plugins"]
    assert any("forms" in p for p in plugins)
    assert any("typography" in p for p in plugins)


def test_tailwind_capsule(tailwind_project):
    wr, parsed = _walk(tailwind_project)
    info = TailwindAdapter().extract(wr, parsed)
    section = TailwindAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "TAILWIND" in section
    assert "brand" in section
    assert "spacing" in section


# ---------------- Docker Compose ----------------

@pytest.fixture
def compose_project(tmp_path):
    (tmp_path / "docker-compose.yml").write_text(
        "version: '3.9'\n"
        "services:\n"
        "  api:\n"
        "    build: ./backend\n"
        "    ports:\n"
        "      - '8000:8000'\n"
        "    depends_on:\n"
        "      - db\n"
        "      - redis\n"
        "    volumes:\n"
        "      - ./backend:/app\n"
        "      - logs:/var/log/api\n"
        "  db:\n"
        "    image: postgres:15-alpine\n"
        "    ports:\n"
        "      - '5432:5432'\n"
        "    volumes:\n"
        "      - pgdata:/var/lib/postgresql/data\n"
        "  redis:\n"
        "    image: redis:7\n"
        "    ports:\n"
        "      - '6379:6379'\n"
        "volumes:\n"
        "  pgdata:\n"
        "  logs:\n"
    )
    return tmp_path


def test_compose_detect(compose_project):
    wr, parsed = _walk(compose_project)
    assert DockerComposeAdapter.detect(wr, parsed) is True


def test_compose_extract(compose_project):
    wr, parsed = _walk(compose_project)
    info = DockerComposeAdapter().extract(wr, parsed)
    names = {e.name for e in info.entries}
    assert {"api", "db", "redis"}.issubset(names)
    db = next(e for e in info.entries if e.name == "db")
    assert db.meta["image"] == "postgres:15-alpine"
    api = next(e for e in info.entries if e.name == "api")
    assert "db" in api.meta["depends_on"]
    assert "redis" in api.meta["depends_on"]
    assert api.meta["volumes_count"] == 2


def test_compose_capsule(compose_project):
    wr, parsed = _walk(compose_project)
    info = DockerComposeAdapter().extract(wr, parsed)
    section = DockerComposeAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "DOCKER-COMPOSE" in section
    assert "api" in section
    assert "postgres:15-alpine" in section
    assert "depends_on" in section


# ---------------- Cross-cutting ----------------

@pytest.mark.parametrize("adapter_cls", [
    SQLAlchemyAdapter, PydanticAdapter, VueAdapter,
    TailwindAdapter, DockerComposeAdapter,
])
def test_adapter_validate_class(adapter_cls):
    errors = adapter_cls.validate_class()
    assert errors == [], f"{adapter_cls.__name__}: {errors}"


@pytest.mark.parametrize("adapter_cls", [
    SQLAlchemyAdapter, PydanticAdapter, VueAdapter,
    TailwindAdapter, DockerComposeAdapter,
])
def test_adapter_skips_unrelated_project(adapter_cls, tmp_path):
    (tmp_path / "x.py").write_text("def f(): pass\n")
    wr, parsed = _walk(tmp_path)
    assert adapter_cls.detect(wr, parsed) is False
    info = adapter_cls().extract(wr, parsed)
    assert info.entries == []
