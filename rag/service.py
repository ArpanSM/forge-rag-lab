"""Service layer that wires corpus, retrieval, generation and the API."""

from __future__ import annotations

import importlib.util
import logging
import os
from collections.abc import Mapping
from pathlib import Path

from rag.bm25 import BM25Index
from rag.chunking import baseline_chunks, structure_chunks
from rag.corpus import Corpus
from rag.embeddings import Embedder, HashingEmbedder, build_embedder
from rag.generation import AnswerGenerator
from rag.models import Answer, PipelineName, RetrievedBlock
from rag.pipelines import BaselinePipeline, FixedPipeline
from rag.providers import FallbackProvider, LLMProvider, build_provider_chain
from rag.retrieval import (
    DEFAULT_CANDIDATE_K,
    DEFAULT_TOP_K,
    CrossEncoderReranker,
    HybridRetriever,
    NoopReranker,
    Reranker,
)
from rag.vector_store import InMemoryVectorStore, QdrantVectorStore, VectorStore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_PATH = PROJECT_ROOT / "data" / "manifests" / "corpus.json"

logger = logging.getLogger(__name__)


class UnknownTenantError(ValueError):
    """The request named a tenant that is not part of the corpus."""


class RagService:
    """Owns both retrieval indexes and exposes pipeline-agnostic operations."""

    def __init__(
        self,
        corpus: Corpus,
        provider: LLMProvider,
        *,
        embedder: Embedder | None = None,
        fixed_store: VectorStore | None = None,
        baseline_store: VectorStore | None = None,
        reranker: Reranker | None = None,
        fixed_top_k: int = DEFAULT_TOP_K,
        baseline_top_k: int = 6,
        candidate_k: int = DEFAULT_CANDIDATE_K,
        index: bool = True,
    ) -> None:
        self.corpus = corpus
        self.provider = provider
        self.embedder = embedder or HashingEmbedder()
        self.fixed_store = fixed_store or InMemoryVectorStore(dimension=self.embedder.dimension)
        self.baseline_store = baseline_store or InMemoryVectorStore(
            dimension=self.embedder.dimension
        )
        self.fixed_retriever = HybridRetriever(
            self.embedder,
            self.fixed_store,
            bm25=BM25Index(),
            reranker=reranker or NoopReranker(),
        )
        self.baseline_retriever = HybridRetriever(
            self.embedder,
            self.baseline_store,
            bm25=None,
            reranker=NoopReranker(),
        )
        self.generator = AnswerGenerator(provider)
        self.fixed_pipeline = FixedPipeline(
            self.fixed_retriever,
            self.generator,
            versions=corpus.versions,
            top_k=fixed_top_k,
            candidate_k=candidate_k,
        )
        self.baseline_pipeline = BaselinePipeline(
            self.baseline_retriever,
            self.generator,
            top_k=baseline_top_k,
            candidate_k=candidate_k,
        )
        self.indexed_blocks = 0
        self.indexed_baseline_chunks = 0
        if index:
            self.reindex()

    def reindex(self) -> tuple[int, int]:
        self.indexed_blocks = self.fixed_retriever.index(structure_chunks(self.corpus))
        self.indexed_baseline_chunks = self.baseline_retriever.index(baseline_chunks(self.corpus))
        return self.indexed_blocks, self.indexed_baseline_chunks

    @property
    def provider_name(self) -> str:
        if isinstance(self.provider, FallbackProvider):
            return self.provider.primary_name
        return self.provider.name

    def health(self) -> dict[str, str]:
        fixed_status = self.fixed_store.status()
        baseline_status = self.baseline_store.status()
        healthy = fixed_status == "ok" and baseline_status == "ok"
        return {
            "status": "ok" if healthy else "degraded",
            "version": "0.1.0",
            "qdrant": fixed_status if fixed_status == baseline_status else "degraded",
            "model_provider": self.provider_name,
        }

    def query(self, tenant_id: str, question: str, pipeline: PipelineName = "fixed") -> Answer:
        if not self.corpus.has_tenant(tenant_id):
            raise UnknownTenantError(f"unknown tenant: {tenant_id}")
        if pipeline == "baseline":
            return self.baseline_pipeline.answer(question, tenant_id=tenant_id)
        return self.fixed_pipeline.answer(question, tenant_id=tenant_id)

    def get_block(
        self,
        *,
        tenant_id: str,
        doc_id: str,
        block_id: str,
        version: str | None = None,
    ) -> RetrievedBlock | None:
        if not self.corpus.has_tenant(tenant_id):
            return None
        if version is not None:
            return self.corpus.get_block(tenant_id, doc_id, version, block_id)
        return self.corpus.get_current_block(tenant_id, doc_id, block_id)


def build_service_from_env(environ: Mapping[str, str] | None = None) -> RagService:
    """Build the production service from environment configuration."""
    env = os.environ if environ is None else environ
    _load_dotenv()

    corpus_path = Path(env.get("CORPUS_PATH", DEFAULT_CORPUS_PATH))
    corpus = Corpus.from_path(corpus_path) if corpus_path.exists() else Corpus.empty()

    if not corpus.documents:
        return RagService(
            corpus,
            build_provider_chain(env),
            embedder=HashingEmbedder(),
            fixed_store=InMemoryVectorStore(),
            baseline_store=InMemoryVectorStore(),
            reranker=NoopReranker(),
        )

    embedder = _build_embedder(env)
    fixed_store, baseline_store = _build_stores(env, embedder.dimension)
    reranker_name = env.get("RERANKER", "bge").strip().lower()
    if reranker_name == "noop" or not _module_available("sentence_transformers"):
        if reranker_name != "noop":
            logger.warning("sentence-transformers is not installed; using NoopReranker")
        reranker: Reranker = NoopReranker()
    else:
        reranker = CrossEncoderReranker()
    return RagService(
        corpus,
        build_provider_chain(env),
        embedder=embedder,
        fixed_store=fixed_store,
        baseline_store=baseline_store,
        reranker=reranker,
    )


def _build_embedder(env: Mapping[str, str]) -> Embedder:
    name = env.get("EMBEDDER", "bge-m3")
    if name.strip().lower() in {"bge-m3", "bge", "bgem3"} and not _module_available(
        "sentence_transformers"
    ):
        logger.warning(
            "sentence-transformers is not installed; using HashingEmbedder for retrieval"
        )
        return HashingEmbedder()
    return build_embedder(name)


def _module_available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


def _build_stores(env: Mapping[str, str], dimension: int) -> tuple[VectorStore, VectorStore]:
    if env.get("VECTOR_STORE", "").strip().lower() == "memory":
        return InMemoryVectorStore(dimension), InMemoryVectorStore(dimension)

    url = env.get("QDRANT_URL")
    if not url or not _module_available("qdrant_client"):
        if url:
            logger.warning("qdrant-client is not installed; using in-memory vector stores")
        return InMemoryVectorStore(dimension), InMemoryVectorStore(dimension)

    collection = env.get("QDRANT_COLLECTION", "helios_blocks")
    api_key = env.get("QDRANT_API_KEY") or None
    return (
        QdrantVectorStore(
            url=url,
            api_key=api_key,
            collection=collection,
            dimension=dimension,
        ),
        QdrantVectorStore(
            url=url,
            api_key=api_key,
            collection=f"{collection}_baseline",
            dimension=dimension,
        ),
    )


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - optional dependency
        return
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def build_default_service() -> RagService:
    return build_service_from_env()


def build_service(
    corpus: Corpus,
    provider: LLMProvider,
    *,
    embedder: Embedder | None = None,
) -> RagService:
    """Small convenience factory used by examples and tests."""
    return RagService(corpus, provider, embedder=embedder)
