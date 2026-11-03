from __future__ import annotations

import os
from pathlib import Path

import pytest

from rag.corpus import Corpus
from rag.embeddings import HashingEmbedder
from rag.providers import FakeProvider
from rag.service import RagService

# Keep the suite offline and fast even when optional retrieval dependencies are
# installed or a developer has a local .env file.
os.environ.setdefault("EMBEDDER", "hashing")
os.environ.setdefault("RERANKER", "noop")
os.environ.setdefault("VECTOR_STORE", "memory")
os.environ["MODEL_PROVIDER"] = "none"
for _provider_key in ("GEMINI_API_KEY", "OPENROUTER_API_KEY", "GROQ_API_KEY"):
    os.environ[_provider_key] = ""
os.environ["OLLAMA_BASE_URL"] = ""

FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "corpus.json"


@pytest.fixture
def corpus() -> Corpus:
    return Corpus.from_path(FIXTURE_CORPUS)


@pytest.fixture
def service_factory(corpus: Corpus):
    def build(response=None, *, provider: FakeProvider | None = None) -> RagService:
        selected = provider or FakeProvider(response)
        return RagService(corpus, selected, embedder=HashingEmbedder())

    return build
