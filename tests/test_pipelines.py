from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag.corpus import Corpus
from rag.embeddings import HashingEmbedder
from rag.models import Answer
from rag.pipelines import version_filter
from rag.prompts import FIXED_SYSTEM_PROMPT
from rag.providers import FakeProvider
from rag.service import RagService, UnknownTenantError, build_service_from_env

FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "corpus.json"


def _payload(claim_text: str, ref: str, quote: str, answer: str) -> str:
    return json.dumps(
        {
            "answerable": True,
            "answer": answer,
            "claims": [
                {
                    "claim_id": "c1",
                    "text": claim_text,
                    "citations": [{"ref": ref, "quote": quote}],
                }
            ],
        }
    )


def _service(corpus: Corpus, fixed: str, baseline: str) -> tuple[RagService, FakeProvider]:
    def respond(system_prompt: str, user_prompt: str) -> str:
        return fixed if system_prompt == FIXED_SYSTEM_PROMPT else baseline

    provider = FakeProvider(respond)
    return (
        RagService(corpus, provider, embedder=HashingEmbedder()),
        provider,
    )


FIXED_API_ANSWER = _payload(
    "The old key remains valid for 24 hours.",
    "helios-api-keys@v3#b4",
    "Rotated keys remain valid for 24 hours after rotation.",
    "The old key remains valid for 24 hours.",
)
BASELINE_SSO_ANSWER = _payload(
    "Admins may opt out of SSO.",
    "helios-sso-policy@v2#b1",
    "Admins may opt out of SSO until 2026-04-01 by contacting support.",
    "Admins may opt out until April 2026.",
)


def test_fixed_pipeline_returns_current_citation(corpus: Corpus) -> None:
    service, _ = _service(corpus, FIXED_API_ANSWER, BASELINE_SSO_ANSWER)

    answer = service.query("northwind", "How long do rotated keys stay valid?", "fixed")

    assert answer.abstained is False
    assert answer.pipeline == "fixed"
    citation = answer.claims[0].citations[0]
    assert citation.version == "v3"
    assert citation.page == 2
    assert citation.block_id == "b4"


def test_fixed_pipeline_supports_explicit_old_version(corpus: Corpus) -> None:
    fixed = _payload(
        "In v2 the old key stops immediately.",
        "helios-api-keys@v2#b2",
        "The old key stops working immediately.",
        "In v2 the old key stops immediately.",
    )
    service, _ = _service(corpus, fixed, BASELINE_SSO_ANSWER)

    answer = service.query("northwind", "How do I rotate an API key in v2?", "fixed")

    assert answer.abstained is False
    citation = answer.claims[0].citations[0]
    assert citation.version == "v2"
    assert citation.doc_id == "helios-api-keys"


def test_fixed_pipeline_rejects_stale_citation_by_default(corpus: Corpus) -> None:
    stale = _payload(
        "Admins may opt out.",
        "helios-sso-policy@v2#b1",
        "Admins may opt out of SSO until 2026-04-01 by contacting support.",
        "Admins may opt out.",
    )
    service, _ = _service(corpus, stale, BASELINE_SSO_ANSWER)

    answer = service.query("northwind", "Can admins opt out of SSO?", "fixed")

    assert answer.abstained is True
    assert answer.claims == []


def test_baseline_pipeline_returns_stale_citation(corpus: Corpus) -> None:
    service, provider = _service(corpus, FIXED_API_ANSWER, BASELINE_SSO_ANSWER)

    answer = service.query("northwind", "Can admins opt out of SSO?", "baseline")

    assert answer.abstained is False
    assert answer.pipeline == "baseline"
    citation = answer.claims[0].citations[0]
    assert citation.version == "v2"
    assert citation.doc_id == "helios-sso-policy"
    baseline_prompt = provider.calls[0][1]
    assert "Can admins opt out of SSO?" in baseline_prompt


def test_baseline_pipeline_never_abstains(corpus: Corpus) -> None:
    baseline = json.dumps({"answerable": False, "answer": "", "claims": []})
    service, _ = _service(corpus, FIXED_API_ANSWER, baseline)

    answer = service.query("northwind", "Can admins opt out of SSO?", "baseline")

    assert isinstance(answer, Answer)
    assert answer.abstained is False
    assert answer.answer


def test_explicit_version_filter() -> None:
    assert version_filter("How do I rotate a key in v2?", ["v1", "v2", "v3"]) == (
        {"v2"},
        False,
    )
    assert version_filter("What changed between v2 and v3?", ["v1", "v2", "v3"]) == (
        {"v2", "v3"},
        False,
    )
    assert version_filter("How do I rotate a key?", ["v1", "v2", "v3"]) == (None, True)


def test_service_rejects_unknown_tenant(corpus: Corpus) -> None:
    service, _ = _service(corpus, FIXED_API_ANSWER, BASELINE_SSO_ANSWER)

    with pytest.raises(UnknownTenantError):
        service.query("globex", "Hello", "fixed")


def test_service_health_and_counts(corpus: Corpus) -> None:
    service, _ = _service(corpus, FIXED_API_ANSWER, BASELINE_SSO_ANSWER)

    health = service.health()
    assert health["status"] == "ok"
    assert health["qdrant"] == "ok"
    assert health["model_provider"] == "fake"
    assert service.indexed_blocks == 18
    assert service.indexed_baseline_chunks == 18


def test_build_service_from_env_offline() -> None:
    service = build_service_from_env(
        {
            "CORPUS_PATH": str(FIXTURE_CORPUS),
            "EMBEDDER": "hashing",
            "RERANKER": "noop",
            "VECTOR_STORE": "memory",
        }
    )

    assert len(service.corpus.documents) == 9
    assert service.indexed_blocks == 18
    assert service.health()["model_provider"] == "none"
    assert service.query("northwind", "How long do rotated keys stay valid?", "fixed").abstained


def test_service_get_block_respects_tenant(corpus: Corpus) -> None:
    service, _ = _service(corpus, FIXED_API_ANSWER, BASELINE_SSO_ANSWER)

    block = service.get_block(
        tenant_id="northwind",
        doc_id="helios-api-keys",
        block_id="b4",
    )
    assert block is not None
    assert block.version == "v3"
    assert service.get_block(tenant_id="acme", doc_id="helios-api-keys", block_id="b4") is None


def test_empty_corpus_fixed_abstains(corpus: Corpus) -> None:
    service = RagService(Corpus.empty(), FakeProvider(), embedder=HashingEmbedder())

    answer = service.query("northwind", "Anything?", "fixed")

    assert answer.abstained is True
    assert service.indexed_blocks == 0


def test_provider_failure_is_contained(corpus: Corpus) -> None:
    provider = FakeProvider(error=RuntimeError("provider down"))
    service = RagService(corpus, provider, embedder=HashingEmbedder())

    fixed = service.query("northwind", "How long do rotated keys stay valid?", "fixed")
    baseline = service.query("northwind", "How long do rotated keys stay valid?", "baseline")

    assert fixed.abstained is True
    assert baseline.abstained is False


def test_fixed_uses_both_prompts_for_fixed_and_baseline(corpus: Corpus) -> None:
    calls: list[tuple[str, str]] = []

    def respond(system_prompt: str, user_prompt: str) -> str:
        calls.append((system_prompt, user_prompt))
        return FIXED_API_ANSWER

    provider = FakeProvider(respond)
    service = RagService(corpus, provider, embedder=HashingEmbedder())

    service.query("northwind", "How long do rotated keys stay valid?", "fixed")
    service.query("northwind", "How long do rotated keys stay valid?", "baseline")

    assert calls[0][0] == FIXED_SYSTEM_PROMPT
    assert calls[0][0] != calls[1][0]
    assert "untrusted" in calls[0][1].lower()
