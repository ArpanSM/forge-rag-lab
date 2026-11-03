"""Grounded answer generation, citation validation, abstention and injection guard."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections.abc import Iterator, Sequence

from rag.models import Answer, Citation, Claim, PipelineName, RetrievedBlock
from rag.prompts import (
    BASELINE_SYSTEM_PROMPT,
    FIXED_SYSTEM_PROMPT,
    build_baseline_prompt,
    build_fixed_prompt,
)
from rag.providers import Completion, LLMProvider
from rag.text import normalize_whitespace, quote_is_supported, short_quote

logger = logging.getLogger(__name__)

ABSTENTION_ANSWER = "I could not find enough evidence to answer that."
BASELINE_FALLBACK_ANSWER = "I could not find a supported answer in the retrieved context."

_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "ignore_instructions",
        re.compile(
            r"\b(ignore|disregard|forget)\b.{0,40}"
            r"\b(previous|prior|above|system|developer)\b.{0,30}"
            r"\b(instructions?|prompts?|rules?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "system_prompt",
        re.compile(r"\b(system|developer)\s+prompt\b", re.IGNORECASE),
    ),
    (
        "role_change",
        re.compile(
            r"\byou are now\b|\bact as\b.{0,30}\b(system|admin|developer)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reveal_secret",
        re.compile(
            r"\b(reveal|leak|dump|print)\b.{0,30}"
            r"\b(system prompt|hidden prompt|secret|password|credential)",
            re.IGNORECASE,
        ),
    ),
    (
        "override_policy",
        re.compile(
            r"\b(override|bypass|ignore)\b.{0,30}\b(policy|rules?|instructions?|guardrails?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "suppress_citation",
        re.compile(r"\bdo not\b.{0,20}\b(cite|mention|quote|tell)\b", re.IGNORECASE),
    ),
    (
        "new_instructions",
        re.compile(r"\bnew instructions?\b|\bfrom now on\b", re.IGNORECASE),
    ),
    (
        "instruction_directive",
        re.compile(
            r"\b(when asked|if asked|then say|then answer|answer that|respond with|reply with)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "exfiltrate",
        re.compile(r"\bexfiltrate\b", re.IGNORECASE),
    ),
)

_REMOVED_INSTRUCTION = "[untrusted instruction removed]"
_CITATION_REF_RE = re.compile(r"([A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+#[A-Za-z0-9_.-]+)")


def detect_injection(text: str) -> list[str]:
    """Return the labels of prompt-injection heuristics that match ``text``."""
    return [label for label, pattern in _INJECTION_PATTERNS if pattern.search(text)]


def sanitize_text(text: str) -> tuple[str, list[str]]:
    """Replace sentences that look like injected instructions with a marker."""
    flags = detect_injection(text)
    if not flags:
        return text, []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    cleaned = [
        _REMOVED_INSTRUCTION if detect_injection(sentence) else sentence for sentence in sentences
    ]
    return " ".join(cleaned), flags


def sanitize_blocks(
    blocks: Sequence[RetrievedBlock],
) -> tuple[list[RetrievedBlock], list[str]]:
    cleaned: list[RetrievedBlock] = []
    flags: list[str] = []
    for block in blocks:
        text, block_flags = sanitize_text(block.text)
        flags.extend(block_flags)
        if block_flags:
            cleaned.append(block.model_copy(update={"text": text}))
        else:
            cleaned.append(block)
    return cleaned, sorted(set(flags))


def parse_json_object(text: str) -> dict[str, object] | None:
    """Parse a JSON object from plain text, code fences or surrounding prose."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed

    decoder = json.JSONDecoder()
    for index, character in enumerate(stripped):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate
    return None


class EvidenceIndex:
    """Resolve model-supplied citation references against the retrieved evidence only."""

    def __init__(self, blocks: Sequence[RetrievedBlock]) -> None:
        self.blocks = list(blocks)
        self._by_ref = {block.ref: block for block in self.blocks}
        self._by_block_id: dict[str, list[RetrievedBlock]] = {}
        self._by_doc_block: dict[tuple[str, str], list[RetrievedBlock]] = {}
        for block in self.blocks:
            self._by_block_id.setdefault(block.block_id, []).append(block)
            self._by_doc_block.setdefault((block.doc_id, block.block_id), []).append(block)

    def resolve(self, reference: object) -> RetrievedBlock | None:
        if not isinstance(reference, str):
            return None
        normalized = _normalize_ref(reference)
        if not normalized:
            return None
        if normalized in self._by_ref:
            return self._by_ref[normalized]

        if "#" in normalized:
            document_part, block_id = normalized.rsplit("#", 1)
            if "@" not in document_part:
                candidates = self._by_doc_block.get((document_part, block_id), [])
                if len(candidates) == 1:
                    return candidates[0]
                return None

        candidates = self._by_block_id.get(normalized, [])
        if len(candidates) == 1:
            return candidates[0]
        return None


def resolve_citations(raw_citations: object, evidence: EvidenceIndex) -> list[Citation]:
    """Resolve citation objects or strings to verified citations against evidence."""
    if raw_citations is None:
        return []
    if isinstance(raw_citations, (str, dict)):
        items: list[object] = [raw_citations]
    elif isinstance(raw_citations, Sequence):
        items = list(raw_citations)
    else:
        return []

    citations: list[Citation] = []
    seen: set[tuple[str, str, str]] = set()
    for item in _flatten_items(items):
        reference, quote = _citation_parts(item)
        block = evidence.resolve(reference)
        if block is None:
            continue
        cleaned = normalize_whitespace(quote)
        if cleaned and not quote_is_supported(cleaned, block.text):
            # A quote that does not appear in the cited block usually means the
            # model picked the wrong block; do not silently relocate the quote.
            continue
        if not cleaned:
            cleaned = short_quote(block.text)
        key = (block.doc_id, block.version, block.block_id)
        if key in seen:
            continue
        seen.add(key)
        citations.append(_make_citation(block, cleaned))
    return citations


def _flatten_items(items: Sequence[object]) -> Iterator[object]:
    """Flatten nested citation arrays emitted by some small models."""
    for item in items:
        if isinstance(item, (list, tuple)):
            yield from _flatten_items(item)
        else:
            yield item


def _citation_parts(item: object) -> tuple[object, str]:
    if isinstance(item, str):
        return item, ""
    if not isinstance(item, dict):
        return None, ""
    ref = item.get("ref") or item.get("citation_id") or item.get("id") or item.get("block_ref")
    if ref is None and item.get("block_id"):
        block_id = str(item["block_id"])
        doc_id = item.get("doc_id")
        version = item.get("version")
        if doc_id and version:
            ref = f"{doc_id}@{version}#{block_id}"
        else:
            ref = block_id
    quote = item.get("quote") or item.get("text") or ""
    return ref, str(quote)


def _make_citation(block: RetrievedBlock, quote: str) -> Citation:
    return Citation(
        doc_id=block.doc_id,
        title=block.title,
        version=block.version,
        page=block.page,
        block_id=block.block_id,
        anchor=block.anchor,
        quote=quote,
    )


def _normalize_ref(reference: str) -> str:
    value = reference.strip().strip("\"'`")
    value = value.removeprefix("[").removesuffix("]")
    value = value.removeprefix("citation:").strip()

    # Small models often wrap the reference in prose, for example
    # "[helios-webhooks@v3#b4] Webhooks — Event types (page 2)". Extract the
    # stable doc@version#block shape before doing anything else.
    match = _CITATION_REF_RE.search(value)
    if match:
        return match.group(1)

    # Also tolerate a schema label such as "@block_id" appended to a ref.
    value = re.sub(r"@(block_id|block|id)\s*$", "", value, flags=re.IGNORECASE)
    if "#" in value:
        document_part, block_part = value.split("#", 1)
        block_part = re.split(r"[@\s(]", block_part, maxsplit=1)[0]
        value = f"{document_part}#{block_part}"
    return value


class AnswerGenerator:
    """Generate an :class:`Answer` from retrieved evidence and one LLM provider."""

    def __init__(
        self,
        provider: LLMProvider,
        *,
        abstention_answer: str = ABSTENTION_ANSWER,
    ) -> None:
        self.provider = provider
        self.abstention_answer = abstention_answer

    def generate(
        self,
        question: str,
        blocks: Sequence[RetrievedBlock],
        *,
        tenant_id: str,
        pipeline: PipelineName = "fixed",
        trace_id: str | None = None,
    ) -> Answer:
        started = time.perf_counter()
        trace = trace_id or new_trace_id()
        if pipeline == "fixed":
            evidence_blocks, injection_flags = sanitize_blocks(blocks)
        else:
            evidence_blocks = list(blocks)
            injection_flags = []

        if pipeline == "fixed" and not evidence_blocks:
            return self._abstain(
                model=self.provider.model,
                trace_id=trace,
                started=started,
                injection_detected=False,
            )

        system_prompt = FIXED_SYSTEM_PROMPT if pipeline == "fixed" else BASELINE_SYSTEM_PROMPT
        user_prompt = (
            build_fixed_prompt(question, evidence_blocks, tenant_id)
            if pipeline == "fixed"
            else build_baseline_prompt(question, evidence_blocks, tenant_id)
        )

        try:
            completion = self.provider.complete(system_prompt, user_prompt)
        except Exception as exc:  # noqa: BLE001 - a provider failure must not crash the API
            logger.warning("provider %s failed: %s", self.provider.name, exc)
            if pipeline == "fixed":
                return self._abstain(
                    model=self.provider.model,
                    trace_id=trace,
                    started=started,
                    injection_detected=bool(injection_flags),
                )
            return self._baseline_failure(
                trace_id=trace,
                started=started,
                model=self.provider.model,
            )

        payload = parse_json_object(completion.text)
        if payload is None:
            if pipeline == "fixed":
                return self._abstain(
                    model=completion.model,
                    trace_id=trace,
                    started=started,
                    injection_detected=bool(injection_flags),
                )
            return self._baseline_from_text(
                completion.text,
                model=completion.model,
                trace_id=trace,
                started=started,
            )

        evidence_index = EvidenceIndex(evidence_blocks)
        if pipeline == "fixed":
            return self._fixed_answer(
                payload,
                evidence=evidence_index,
                completion=completion,
                trace_id=trace,
                started=started,
                injection_detected=bool(injection_flags),
            )
        return self._baseline_answer(
            payload,
            evidence=evidence_index,
            completion=completion,
            trace_id=trace,
            started=started,
        )

    def _fixed_answer(
        self,
        payload: dict[str, object],
        *,
        evidence: EvidenceIndex,
        completion: Completion,
        trace_id: str,
        started: float,
        injection_detected: bool,
    ) -> Answer:
        if (
            payload.get("answerable") is False
            or payload.get("abstained") is True
            or payload.get("abstain") is True
        ):
            answer_text = str(payload.get("answer") or self.abstention_answer)
            return Answer(
                answer=answer_text,
                abstained=True,
                claims=[],
                latency_ms=_elapsed_ms(started),
                model=completion.model,
                pipeline="fixed",
                trace_id=trace_id,
                injection_detected=injection_detected,
            )

        claims = _claims_from_payload(
            payload,
            evidence=evidence,
            drop_unsupported=True,
        )
        if not claims:
            return self._abstain(
                model=completion.model,
                trace_id=trace_id,
                started=started,
                injection_detected=injection_detected,
            )

        answer_text = str(payload.get("answer") or "").strip()
        if not answer_text:
            answer_text = " ".join(claim.text for claim in claims)
        return Answer(
            answer=answer_text,
            abstained=False,
            claims=claims,
            latency_ms=_elapsed_ms(started),
            model=completion.model,
            pipeline="fixed",
            trace_id=trace_id,
            injection_detected=injection_detected,
        )

    def _baseline_answer(
        self,
        payload: dict[str, object],
        *,
        evidence: EvidenceIndex,
        completion: Completion,
        trace_id: str,
        started: float,
    ) -> Answer:
        claims = _claims_from_payload(
            payload,
            evidence=evidence,
            drop_unsupported=False,
        )
        answer_text = str(payload.get("answer") or "").strip()
        if not answer_text:
            answer_text = " ".join(claim.text for claim in claims)
        if not claims and answer_text:
            claims = [Claim(claim_id="c1", text=answer_text, citations=[])]
        if not answer_text:
            answer_text = BASELINE_FALLBACK_ANSWER
        return Answer(
            answer=answer_text,
            abstained=False,
            claims=claims,
            latency_ms=_elapsed_ms(started),
            model=completion.model,
            pipeline="baseline",
            trace_id=trace_id,
            injection_detected=False,
        )

    def _abstain(
        self,
        *,
        model: str,
        trace_id: str,
        started: float,
        injection_detected: bool,
    ) -> Answer:
        return Answer(
            answer=self.abstention_answer,
            abstained=True,
            claims=[],
            latency_ms=_elapsed_ms(started),
            model=model,
            pipeline="fixed",
            trace_id=trace_id,
            injection_detected=injection_detected,
        )

    def _baseline_from_text(
        self,
        text: str,
        *,
        model: str,
        trace_id: str,
        started: float,
    ) -> Answer:
        answer_text = text.strip() or BASELINE_FALLBACK_ANSWER
        return Answer(
            answer=answer_text,
            abstained=False,
            claims=[Claim(claim_id="c1", text=answer_text, citations=[])],
            latency_ms=_elapsed_ms(started),
            model=model,
            pipeline="baseline",
            trace_id=trace_id,
            injection_detected=False,
        )

    def _baseline_failure(self, *, trace_id: str, started: float, model: str) -> Answer:
        return Answer(
            answer=BASELINE_FALLBACK_ANSWER,
            abstained=False,
            claims=[],
            latency_ms=_elapsed_ms(started),
            model=model,
            pipeline="baseline",
            trace_id=trace_id,
            injection_detected=False,
        )


def _claims_from_payload(
    payload: dict[str, object],
    *,
    evidence: EvidenceIndex,
    drop_unsupported: bool,
) -> list[Claim]:
    raw_claims = payload.get("claims")
    items: list[object]
    if isinstance(raw_claims, list):
        items = raw_claims
    elif isinstance(raw_claims, dict):
        items = [raw_claims]
    elif isinstance(payload.get("citations"), (list, dict, str)):
        items = [
            {
                "claim_id": "c1",
                "text": payload.get("answer") or "",
                "citations": payload.get("citations"),
            }
        ]
    else:
        items = []

    claims: list[Claim] = []
    used_ids: set[str] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("claim") or "").strip()
        if not text:
            continue
        raw_id = str(item.get("claim_id") or item.get("id") or "").strip()
        claim_id = raw_id or f"c{index}"
        if claim_id in used_ids:
            claim_id = f"c{index}"
        used_ids.add(claim_id)

        citations = resolve_citations(
            item.get("citations") or item.get("citation_ids") or item.get("sources"),
            evidence,
        )
        if drop_unsupported and not citations:
            continue
        claims.append(Claim(claim_id=claim_id, text=text, citations=citations))
    return claims


def new_trace_id() -> str:
    """Generate a ULID-shaped, time-sortable trace id without a dependency."""
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    timestamp = int(time.time() * 1000) & ((1 << 48) - 1)
    randomness = int.from_bytes(os.urandom(10), "big")
    value = (timestamp << 80) | randomness
    characters: list[str] = []
    for _ in range(26):
        characters.append(alphabet[value & 31])
        value >>= 5
    return "".join(reversed(characters))


def _elapsed_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1000))


def generate_answer(
    question: str,
    blocks: Sequence[RetrievedBlock],
    *,
    tenant_id: str,
    provider: LLMProvider,
    pipeline: PipelineName = "fixed",
) -> Answer:
    """Convenience wrapper around :class:`AnswerGenerator`."""
    return AnswerGenerator(provider).generate(
        question,
        blocks,
        tenant_id=tenant_id,
        pipeline=pipeline,
    )


__all__ = [
    "ABSTENTION_ANSWER",
    "AnswerGenerator",
    "EvidenceIndex",
    "detect_injection",
    "generate_answer",
    "new_trace_id",
    "parse_json_object",
    "resolve_citations",
    "sanitize_blocks",
    "sanitize_text",
]
