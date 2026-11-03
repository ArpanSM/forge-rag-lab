"""LLM provider abstraction with an OpenAI-compatible transport and fallback chain."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import httpx

GEMINI_DEFAULT_MODEL = "gemini-3.5-flash-lite"
OPENROUTER_DEFAULT_MODEL = "google/gemma-4-31b-it:free"
GROQ_DEFAULT_MODEL = "openai/gpt-oss-120b"
ORCAROUTER_DEFAULT_MODEL = "tencent/hy4-preview-free"
OLLAMA_DEFAULT_MODEL = "qwen3.5:4b"

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
ORCAROUTER_BASE_URL = "https://api.orcarouter.ai/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"


class ProviderError(RuntimeError):
    """A provider could not produce a completion."""


class ProviderUnavailable(ProviderError):
    """A provider is not configured (for example, its API key is missing)."""


class AllProvidersFailed(ProviderError):
    """Every provider in the fallback chain failed."""


@dataclass(frozen=True)
class Completion:
    text: str
    model: str
    provider: str


@runtime_checkable
class LLMProvider(Protocol):
    name: str
    model: str

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
    ) -> Completion: ...


class OpenAICompatibleProvider:
    """Minimal chat-completions client shared by Gemini, OpenRouter, Groq and Ollama."""

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        model: str,
        api_key: str | None = None,
        require_api_key: bool = True,
        timeout: float = 45.0,
        max_tokens: int = 2048,
        extra_headers: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
        json_mode: bool = True,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.require_api_key = require_api_key
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.extra_headers = dict(extra_headers or {})
        self._http_client = http_client
        self.json_mode = json_mode

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
    ) -> Completion:
        if self.require_api_key and not self.api_key:
            raise ProviderUnavailable(f"{self.name}: API key is not configured")

        payload: dict[str, object] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": self.max_tokens,
        }
        if self.json_mode:
            payload["response_format"] = {"type": "json_object"}

        owns_client = self._http_client is None
        client = self._http_client or httpx.Client(timeout=self.timeout)
        try:
            response = self._post(client, payload)
            if response.status_code == 400 and self.json_mode:
                # Some OpenAI-compatible servers reject response_format.
                payload.pop("response_format", None)
                response = self._post(client, payload)
        finally:
            if owns_client:
                client.close()

        if response.status_code >= 400:
            detail = _truncate(response.text)
            raise ProviderError(f"{self.name}: HTTP {response.status_code}: {detail}")
        try:
            body = response.json()
        except ValueError as exc:
            raise ProviderError(f"{self.name}: response was not JSON") from exc

        choices = body.get("choices") or []
        if not choices:
            raise ProviderError(f"{self.name}: response contained no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part) for part in content
            )
        if not isinstance(content, str) or not content.strip():
            raise ProviderError(f"{self.name}: completion was empty")
        return Completion(
            text=content,
            model=str(body.get("model") or self.model),
            provider=self.name,
        )

    def _post(self, client: httpx.Client, payload: dict[str, object]) -> httpx.Response:
        headers = {"Content-Type": "application/json", **self.extra_headers}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            return client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name}: request failed: {type(exc).__name__}") from exc


class GeminiProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = GEMINI_DEFAULT_MODEL,
        **kwargs: object,
    ) -> None:
        super().__init__(
            name="gemini",
            base_url=GEMINI_BASE_URL,
            model=model,
            api_key=api_key,
            require_api_key=True,
            **kwargs,
        )


class OpenRouterProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = OPENROUTER_DEFAULT_MODEL,
        **kwargs: object,
    ) -> None:
        super().__init__(
            name="openrouter",
            base_url=OPENROUTER_BASE_URL,
            model=model,
            api_key=api_key,
            require_api_key=True,
            **kwargs,
        )


class GroqProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = GROQ_DEFAULT_MODEL,
        **kwargs: object,
    ) -> None:
        super().__init__(
            name="groq",
            base_url=GROQ_BASE_URL,
            model=model,
            api_key=api_key,
            require_api_key=True,
            **kwargs,
        )


class OrcaRouterProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = ORCAROUTER_DEFAULT_MODEL,
        **kwargs: object,
    ) -> None:
        super().__init__(
            name="orcarouter",
            base_url=ORCAROUTER_BASE_URL,
            model=model,
            api_key=api_key,
            require_api_key=True,
            **kwargs,
        )


class OllamaProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        *,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_DEFAULT_MODEL,
        **kwargs: object,
    ) -> None:
        super().__init__(
            name="ollama",
            base_url=base_url,
            model=model,
            api_key=None,
            require_api_key=False,
            **kwargs,
        )


class FakeProvider:
    """Deterministic provider for tests; optionally raises or calls a responder."""

    def __init__(
        self,
        response: str | Callable[[str, str], str] | None = None,
        *,
        name: str = "fake",
        model: str = "fake-model",
        error: Exception | None = None,
    ) -> None:
        self._response = response
        self.name = name
        self.model = model
        self.error = error
        self.calls: list[tuple[str, str]] = []

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
    ) -> Completion:
        self.calls.append((system_prompt, user_prompt))
        if self.error is not None:
            raise self.error
        if callable(self._response):
            text = self._response(system_prompt, user_prompt)
        elif self._response is not None:
            text = self._response
        else:
            text = (
                '{"answerable": true, "answer": "Fake answer.", '
                '"claims": [{"claim_id": "c1", "text": "Fake answer.", "citations": []}]}'
            )
        return Completion(text=text, model=self.model, provider=self.name)


class FallbackProvider:
    """Try providers in order; surface the first completion or a combined failure."""

    name = "fallback"

    def __init__(self, providers: Sequence[LLMProvider]) -> None:
        self.providers = tuple(providers)
        self.model = "fallback"

    @property
    def primary_name(self) -> str:
        return self.providers[0].name if self.providers else "none"

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
    ) -> Completion:
        if not self.providers:
            raise AllProvidersFailed("no LLM providers configured")
        failures: list[str] = []
        last_error: Exception | None = None
        for provider in self.providers:
            try:
                completion = provider.complete(system_prompt, user_prompt, temperature=temperature)
            except Exception as exc:  # noqa: BLE001 - fallback must survive any provider error
                failures.append(f"{provider.name}: {type(exc).__name__}")
                last_error = exc
                continue
            self.model = completion.model
            return completion
        message = "all providers failed: " + ", ".join(failures)
        raise AllProvidersFailed(message) from last_error


def build_provider_chain(
    environ: Mapping[str, str] | None = None,
    *,
    include_ollama: bool | None = None,
) -> FallbackProvider:
    """Build the configured fallback chain without making any network calls."""
    env = os.environ if environ is None else environ
    selected = env.get("MODEL_PROVIDER", "gemini").strip().lower()

    candidates: list[LLMProvider] = []
    gemini_key = env.get("GEMINI_API_KEY")
    if gemini_key:
        candidates.append(
            GeminiProvider(
                gemini_key,
                model=env.get("GEMINI_MODEL", GEMINI_DEFAULT_MODEL),
            )
        )
    openrouter_key = env.get("OPENROUTER_API_KEY")
    if openrouter_key:
        candidates.append(
            OpenRouterProvider(
                openrouter_key,
                model=env.get("OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL),
            )
        )
    groq_key = env.get("GROQ_API_KEY")
    if groq_key:
        candidates.append(
            GroqProvider(
                groq_key,
                model=env.get("GROQ_MODEL", GROQ_DEFAULT_MODEL),
            )
        )

    orcarouter_key = env.get("ORCAROUTER_API_KEY")
    if orcarouter_key:
        candidates.append(
            OrcaRouterProvider(
                orcarouter_key,
                model=env.get("ORCAROUTER_MODEL", ORCAROUTER_DEFAULT_MODEL),
            )
        )

    ollama_enabled = include_ollama
    if ollama_enabled is None:
        ollama_enabled = selected == "ollama" or bool(env.get("OLLAMA_BASE_URL"))
    if ollama_enabled:
        candidates.append(
            OllamaProvider(
                base_url=env.get("OLLAMA_BASE_URL", OLLAMA_BASE_URL),
                model=env.get("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL),
            )
        )

    candidates.sort(key=lambda provider: 0 if provider.name == selected else 1)
    return FallbackProvider(candidates)


def _truncate(text: str, limit: int = 300) -> str:
    cleaned = " ".join(text.split())
    return cleaned if len(cleaned) <= limit else cleaned[:limit] + "..."
