from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from rag.corpus import Corpus
from rag.embeddings import HashingEmbedder
from rag.pipeline import answer_to_result, run_question
from rag.providers import FakeProvider
from rag.service import RagService

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "corpus.json"


def _service(corpus: Corpus) -> RagService:
    response = json.dumps(
        {
            "answerable": True,
            "answer": "The old key remains valid for 24 hours.",
            "claims": [
                {
                    "claim_id": "c1",
                    "text": "The old key remains valid for 24 hours.",
                    "citations": [
                        {
                            "ref": "helios-api-keys@v3#b4",
                            "quote": "Rotated keys remain valid for 24 hours after rotation.",
                        }
                    ],
                }
            ],
        }
    )
    return RagService(corpus, FakeProvider(response), embedder=HashingEmbedder())


def test_run_question_maps_answer_to_eval_result(corpus: Corpus) -> None:
    result = run_question(
        {
            "question_id": "q001",
            "tenant_id": "northwind",
            "question": "How long do rotated keys stay valid?",
        },
        _service(corpus),
        "fixed",
    )

    assert result["question_id"] == "q001"
    assert result["pipeline"] == "fixed"
    assert result["abstained"] is False
    assert result["citations"][0]["doc_id"] == "helios-api-keys"
    assert result["citations"][0]["version"] == "v3"
    assert result["citations"][0]["tenant_id"] == "northwind"
    assert result["retrieved"][0]["rank"] == 1
    assert result["retrieved"][0]["text"]
    assert result["model"] == "fake-model"
    assert result["metadata"]["retrieved_count"] == len(result["retrieved"])


def test_answer_to_result_returns_contract_shape(corpus: Corpus) -> None:
    service = _service(corpus)
    answer = service.query("northwind", "How long do rotated keys stay valid?", "fixed")

    result = answer_to_result({"question_id": "q002", "tenant_id": "northwind"}, answer)

    assert set(result) >= {
        "question_id",
        "pipeline",
        "answer",
        "abstained",
        "citations",
        "retrieved",
        "latency_ms",
        "model",
        "trace_id",
    }
    assert result["citations"][0]["anchor"] == "#rotation-grace-period"


def test_pipeline_cli_is_json_in_json_out() -> None:
    env = {
        **os.environ,
        "CORPUS_PATH": str(FIXTURE_CORPUS),
        "EMBEDDER": "hashing",
        "RERANKER": "noop",
        "VECTOR_STORE": "memory",
        "MODEL_PROVIDER": "none",
        "GEMINI_API_KEY": "",
        "OPENROUTER_API_KEY": "",
        "GROQ_API_KEY": "",
        "OLLAMA_BASE_URL": "",
    }
    completed = subprocess.run(
        [sys.executable, "-m", "rag.pipeline", "--json", "--pipeline", "fixed"],
        input=json.dumps(
            {
                "question_id": "q003",
                "tenant_id": "northwind",
                "question": "How long do rotated keys stay valid?",
            }
        ),
        text=True,
        capture_output=True,
        cwd=ROOT,
        env=env,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout.strip())
    assert payload["question_id"] == "q003"
    assert payload["pipeline"] == "fixed"
    assert payload["abstained"] is True
    assert payload["citations"] == []
