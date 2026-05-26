"""Tests for the _vector_db adapter pack — Pinecone, Weaviate, Qdrant, Chroma."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "lensify"
sys.path.insert(0, str(SCRIPTS))

from scripts.walker import walk  # noqa: E402
from scripts.ast_parser import parse_all  # noqa: E402
from scripts.frameworks._vector_db.pinecone import PineconeAdapter  # noqa: E402
from scripts.frameworks._vector_db.weaviate import WeaviateAdapter  # noqa: E402
from scripts.frameworks._vector_db.qdrant import QdrantAdapter  # noqa: E402
from scripts.frameworks._vector_db.chroma import ChromaAdapter  # noqa: E402


def _walk(p):
    wr = walk(str(p))
    return wr, parse_all(wr.code_files)


# ---------------- Pinecone ----------------

@pytest.fixture
def pinecone_project(tmp_path):
    (tmp_path / "rag.py").write_text(
        "from pinecone import Pinecone\n"
        "import pinecone\n"
        "\n"
        "pc = Pinecone(api_key='xxx')\n"
        "pinecone.init(api_key='xxx', environment='us-west')\n"
        "\n"
        "pc.create_index(name='docs', dimension=1536, metric='cosine')\n"
        "pc.create_index(name='code', dimension=768, metric='dotproduct')\n"
        "\n"
        "idx = pc.Index('docs')\n"
        "idx2 = pinecone.Index('legacy')\n"
        "\n"
        "idx.upsert(vectors=[(1, [0.1]*1536)])\n"
        "idx.upsert(vectors=[(2, [0.2]*1536)])\n"
        "idx.query(vector=[0.3]*1536, top_k=5)\n"
    )
    return tmp_path


def test_pinecone_detect(pinecone_project):
    wr, parsed = _walk(pinecone_project)
    assert PineconeAdapter.detect(wr, parsed) is True


def test_pinecone_extract(pinecone_project):
    wr, parsed = _walk(pinecone_project)
    info = PineconeAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    assert "client" in kinds
    assert "create" in kinds
    assert "index" in kinds
    assert "docs" in info.meta["indexes"]
    assert "code" in info.meta["indexes"]
    assert "legacy" in info.meta["indexes"]
    assert info.meta["ops"]["upsert"] == 2
    assert info.meta["ops"]["query"] == 1


def test_pinecone_capsule(pinecone_project):
    wr, parsed = _walk(pinecone_project)
    info = PineconeAdapter().extract(wr, parsed)
    section = PineconeAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "PINECONE" in section
    assert "docs" in section
    assert "dim=1536" in section


# ---------------- Weaviate ----------------

@pytest.fixture
def weaviate_project(tmp_path):
    (tmp_path / "vstore.py").write_text(
        "import weaviate\n"
        "from weaviate import WeaviateClient\n"
        "\n"
        "client = weaviate.connect_to_local()\n"
        "cloud_client = weaviate.connect_to_wcs(cluster_url='x')\n"
        "\n"
        "client.collections.create(name='Article', properties=[])\n"
        "client.collections.create(name='Page', properties=[])\n"
        "articles = client.collections.get('Article')\n"
        "\n"
        "articles.query.near_vector(near_vector=[0.1]*768, limit=5)\n"
        "articles.query.near_text(query='hello', limit=10)\n"
        "articles.query.bm25(query='kw')\n"
    )
    return tmp_path


def test_weaviate_detect(weaviate_project):
    wr, parsed = _walk(weaviate_project)
    assert WeaviateAdapter.detect(wr, parsed) is True


def test_weaviate_extract(weaviate_project):
    wr, parsed = _walk(weaviate_project)
    info = WeaviateAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    assert "client" in kinds
    assert "collection" in kinds
    assert "Article" in info.meta["collections_referenced"]
    assert "Page" in info.meta["collections_referenced"]
    assert info.meta["query_counts"]["near_vector"] == 1
    assert info.meta["query_counts"]["near_text"] == 1
    assert info.meta["query_counts"]["bm25"] == 1


def test_weaviate_capsule(weaviate_project):
    wr, parsed = _walk(weaviate_project)
    info = WeaviateAdapter().extract(wr, parsed)
    section = WeaviateAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "WEAVIATE" in section
    assert "Article" in section
    assert "near_vector" in section


# ---------------- Qdrant ----------------

@pytest.fixture
def qdrant_project(tmp_path):
    (tmp_path / "vstore.py").write_text(
        "from qdrant_client import QdrantClient\n"
        "from qdrant_client.models import VectorParams, Distance\n"
        "\n"
        "client = QdrantClient(url='http://localhost:6333')\n"
        "\n"
        "client.create_collection(\n"
        "    collection_name='docs',\n"
        "    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),\n"
        ")\n"
        "client.recreate_collection(\n"
        "    collection_name='code',\n"
        "    vectors_config=VectorParams(size=768, distance=Distance.DOT),\n"
        ")\n"
        "\n"
        "client.upsert(collection_name='docs', points=[])\n"
        "client.search(collection_name='docs', query_vector=[0.1]*1536, limit=5)\n"
    )
    return tmp_path


def test_qdrant_detect(qdrant_project):
    wr, parsed = _walk(qdrant_project)
    assert QdrantAdapter.detect(wr, parsed) is True


def test_qdrant_extract(qdrant_project):
    wr, parsed = _walk(qdrant_project)
    info = QdrantAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    assert "client" in kinds
    assert "collection" in kinds
    assert "docs" in info.meta["collections"]
    assert "code" in info.meta["collections"]
    assert "upsert" in info.meta["ops"]
    assert "search" in info.meta["ops"]


def test_qdrant_capsule(qdrant_project):
    wr, parsed = _walk(qdrant_project)
    info = QdrantAdapter().extract(wr, parsed)
    section = QdrantAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "QDRANT" in section
    assert "docs" in section
    assert "size=1536" in section


# ---------------- Chroma ----------------

@pytest.fixture
def chroma_project(tmp_path):
    (tmp_path / "store.py").write_text(
        "import chromadb\n"
        "from chromadb.utils import embedding_functions\n"
        "\n"
        "client = chromadb.PersistentClient(path='./db')\n"
        "remote = chromadb.HttpClient(host='localhost', port=8000)\n"
        "\n"
        "default_ef = embedding_functions.DefaultEmbeddingFunction()\n"
        "docs = client.create_collection(name='documents', embedding_function=default_ef)\n"
        "pages = client.get_or_create_collection(name='pages')\n"
        "old = client.get_collection(name='archive')\n"
        "\n"
        "docs.add(documents=['hello'], ids=['1'])\n"
        "docs.add(documents=['world'], ids=['2'])\n"
        "docs.query(query_texts=['hi'], n_results=3)\n"
        "docs.update(ids=['1'], documents=['hello v2'])\n"
        "docs.delete(ids=['2'])\n"
    )
    return tmp_path


def test_chroma_detect(chroma_project):
    wr, parsed = _walk(chroma_project)
    assert ChromaAdapter.detect(wr, parsed) is True


def test_chroma_extract(chroma_project):
    wr, parsed = _walk(chroma_project)
    info = ChromaAdapter().extract(wr, parsed)
    kinds = {e.kind for e in info.entries}
    classes = {e.meta.get("class") for e in info.entries if e.kind == "client"}
    assert "client" in kinds
    assert "collection" in kinds
    assert "PersistentClient" in classes
    assert "HttpClient" in classes
    assert "documents" in info.meta["collections"]
    assert "pages" in info.meta["collections"]
    assert "archive" in info.meta["collections"]
    assert "default_ef" in info.meta["embedding_functions"]
    assert info.meta["ops"]["add"] == 2
    assert info.meta["ops"]["query"] == 1


def test_chroma_capsule(chroma_project):
    wr, parsed = _walk(chroma_project)
    info = ChromaAdapter().extract(wr, parsed)
    section = ChromaAdapter().capsule_section(info, budget_tokens=600)
    assert section is not None
    assert "CHROMA" in section
    assert "documents" in section
    assert "add×" in section


# ---------------- Cross-cutting ----------------

@pytest.mark.parametrize("adapter_cls", [
    PineconeAdapter, WeaviateAdapter, QdrantAdapter, ChromaAdapter,
])
def test_adapter_validate_class(adapter_cls):
    errors = adapter_cls.validate_class()
    assert errors == [], f"{adapter_cls.__name__}: {errors}"


@pytest.mark.parametrize("adapter_cls", [
    PineconeAdapter, WeaviateAdapter, QdrantAdapter, ChromaAdapter,
])
def test_adapter_skips_unrelated_project(adapter_cls, tmp_path):
    (tmp_path / "x.py").write_text("def f(): pass\n")
    wr, parsed = _walk(tmp_path)
    assert adapter_cls.detect(wr, parsed) is False
    info = adapter_cls().extract(wr, parsed)
    assert info.entries == []
