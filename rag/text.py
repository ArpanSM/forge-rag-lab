"""Small text helpers shared by BM25, embeddings and citation validation."""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_WHITESPACE_RE = re.compile(r"\s+")

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "could",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "if",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "should",
        "than",
        "that",
        "the",
        "their",
        "then",
        "there",
        "these",
        "this",
        "to",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "would",
    }
)


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens, dropping a small English stopword list."""
    return [token for token in _TOKEN_RE.findall(text.lower()) if token not in STOPWORDS]


def normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def short_quote(text: str, max_chars: int = 280) -> str:
    """Return an exact substring suitable for a citation quote."""
    cleaned = normalize_whitespace(text)
    if len(cleaned) <= max_chars:
        return cleaned
    cut = cleaned[:max_chars]
    boundary = cut.rfind(" ")
    if boundary >= max_chars // 2:
        cut = cut[:boundary]
    return cut.rstrip(" ,;:")


def quote_is_supported(quote: str, text: str) -> bool:
    """Check a quote against a block, tolerating whitespace differences."""
    candidate = normalize_whitespace(quote).rstrip("…")
    haystack = normalize_whitespace(text)
    return bool(candidate) and candidate in haystack
