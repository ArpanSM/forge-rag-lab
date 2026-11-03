from __future__ import annotations

import json

import httpx
import pytest

from rag.providers import (
    ORCAROUTER_BASE_URL,
    ORCAROUTER_DEFAULT_MODEL,
    AllProvidersFailed,
    FakeProvider,
    FallbackProvider,
    GeminiProvider,
    OpenAICompatibleProvider,
    OrcaRouterProvider,
    ProviderError,
    ProviderUnavailable,
    build_provider_chain,
)


def test_fake_provider_records_calls() -> None:
    provider = FakeProvider('{"answer": "x"}')

    completion = provider.complete("system", "user")

    assert completion.text == '{"answer": "x"}'
    assert completion.provider == "fake"
    assert provider.calls == [("system", "user")]


def test_fallback_provider_uses_next_provider() -> None:
    first = FakeProvider(error=ProviderError("down"), name="first", model="m1")
    second = FakeProvider('{"answer": "ok"}', name="second", model="m2")
    fallback = FallbackProvider([first, second])

    completion = fallback.complete("system", "user")

    assert completion.provider == "second"
    assert completion.model == "m2"
    assert fallback.model == "m2"
    assert fallback.primary_name == "first"


def test_fallback_provider_all_fail() -> None:
    fallback = FallbackProvider(
        [
            FakeProvider(error=ProviderError("one"), name="one"),
            FakeProvider(error=ProviderError("two"), name="two"),
        ]
    )

    with pytest.raises(AllProvidersFailed, match="one.*two"):
        fallback.complete("system", "user")


def test_fallback_provider_empty() -> None:
    fallback = FallbackProvider([])

    assert fallback.primary_name == "none"
    with pytest.raises(AllProvidersFailed, match="no LLM providers"):
        fallback.complete("system", "user")


def test_openai_compatible_request_shape() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "model": "model-returned",
                "choices": [{"message": {"content": "hello"}}],
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider(
        name="test",
        base_url="https://example.test/v1",
        model="model-configured",
        api_key="secret-key",
        http_client=client,
        json_mode=False,
    )

    completion = provider.complete("system prompt", "user prompt", temperature=0.2)

    assert completion.text == "hello"
    assert completion.model == "model-returned"
    assert completion.provider == "test"
    assert requests[0].url.path == "/v1/chat/completions"
    assert requests[0].headers["authorization"] == "Bearer secret-key"
    body = json.loads(requests[0].content)
    assert body["model"] == "model-configured"
    assert body["temperature"] == 0.2
    assert body["max_tokens"] == 2048
    assert body["messages"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "user prompt"},
    ]
    client.close()


def test_openai_compatible_reasoning_effort() -> None:
    requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"model": "m", "choices": [{"message": {"content": "ok"}}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider(
        name="test",
        base_url="https://example.test/v1",
        model="m",
        api_key="key",
        http_client=client,
        json_mode=False,
        reasoning_effort="none",
    )

    provider.complete("system", "user")

    assert requests[0]["reasoning_effort"] == "none"
    client.close()


def test_openai_compatible_retries_without_json_mode() -> None:
    requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        if "response_format" in body:
            return httpx.Response(400, text="response_format is not supported")
        return httpx.Response(
            200,
            json={"model": "m", "choices": [{"message": {"content": "ok"}}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider(
        name="test",
        base_url="https://example.test/v1",
        model="m",
        api_key="key",
        http_client=client,
        json_mode=True,
    )

    completion = provider.complete("system", "user")

    assert completion.text == "ok"
    assert len(requests) == 2
    assert "response_format" in requests[0]
    assert "response_format" not in requests[1]
    client.close()


def test_openai_compatible_errors() -> None:
    with pytest.raises(ProviderUnavailable, match="API key"):
        OpenAICompatibleProvider(
            name="test",
            base_url="https://example.test/v1",
            model="m",
        ).complete("system", "user")

    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(500, text="boom"))
    )
    provider = OpenAICompatibleProvider(
        name="test",
        base_url="https://example.test/v1",
        model="m",
        api_key="key",
        http_client=client,
        json_mode=False,
    )
    with pytest.raises(ProviderError, match="HTTP 500"):
        provider.complete("system", "user")
    client.close()


def test_openai_compatible_http_transport_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider(
        name="test",
        base_url="https://example.test/v1",
        model="m",
        api_key="key",
        http_client=client,
        json_mode=False,
    )

    with pytest.raises(ProviderError, match="request failed"):
        provider.complete("system", "user")
    client.close()


def test_provider_defaults() -> None:
    gemini = GeminiProvider("key")
    assert gemini.name == "gemini"
    assert gemini.model == "gemini-3.5-flash-lite"
    assert gemini.base_url.endswith("/openai")

    orcarouter = OrcaRouterProvider("key")
    assert orcarouter.name == "orcarouter"
    assert orcarouter.model == ORCAROUTER_DEFAULT_MODEL
    assert orcarouter.base_url == ORCAROUTER_BASE_URL
    assert orcarouter.reasoning_effort == "none"


def test_build_provider_chain_from_environment() -> None:
    empty = build_provider_chain({})
    assert empty.providers == ()
    assert empty.primary_name == "none"

    configured = build_provider_chain(
        {
            "GEMINI_API_KEY": "g",
            "OPENROUTER_API_KEY": "o",
            "GROQ_API_KEY": "q",
            "ORCAROUTER_API_KEY": "r",
        }
    )
    assert [provider.name for provider in configured.providers] == [
        "gemini",
        "openrouter",
        "groq",
        "orcarouter",
    ]

    selected_orcarouter = build_provider_chain(
        {
            "MODEL_PROVIDER": "orcarouter",
            "ORCAROUTER_API_KEY": "r",
        }
    )
    assert selected_orcarouter.primary_name == "orcarouter"

    selected = build_provider_chain(
        {
            "MODEL_PROVIDER": "groq",
            "GEMINI_API_KEY": "g",
            "GROQ_API_KEY": "q",
        }
    )
    assert selected.primary_name == "groq"

    ollama = build_provider_chain({"OLLAMA_BASE_URL": "http://ollama:11434/v1"})
    assert [provider.name for provider in ollama.providers] == ["ollama"]

    selected_ollama = build_provider_chain({"MODEL_PROVIDER": "ollama"})
    assert [provider.name for provider in selected_ollama.providers] == ["ollama"]
