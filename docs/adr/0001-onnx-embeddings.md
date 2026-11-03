# 0001 — ONNX embeddings instead of PyTorch

**Status:** accepted  
**Date:** 2026-11-03

## Context

The RAG lab needs local embeddings and a reranker that run on a CPU-only laptop under a strict
$0 budget. The original plan named BGE-M3, which is usually loaded through
`sentence-transformers` and therefore PyTorch. PyTorch is a large dependency to install just to
embed a 60-page synthetic corpus, and the user explicitly asked for an ONNX path.

## Decision

Use **FastEmbed** with ONNX Runtime for both embeddings and reranking:

- Embeddings: `BAAI/bge-base-en-v1.5` (768 dimensions).
- Reranker: `BAAI/bge-reranker-v2-m3-int8` (INT8 ONNX).
- Keep the deterministic `HashingEmbedder` for unit tests and offline plumbing checks.
- BGE-M3 remains an optional upgrade if an ONNX runtime for it is added later.

## Consequences

- No PyTorch install; much smaller dependency footprint and faster setup.
- BGE-base is smaller than BGE-M3 and may be weaker on multilingual or long-context retrieval.
  The evaluation harness measures the actual effect on this corpus.
- The reranker is an INT8 ONNX model; the `bge-reranker-v2-m3` family is preserved while
  reducing memory and download size.
- The model names are configurable through `EMBEDDER_MODEL` and `RERANKER_MODEL`.

## Alternatives considered

- **BGE-M3 via sentence-transformers / PyTorch:** stronger multilingual model, but a heavy
  dependency and unnecessary for an English synthetic corpus.
- **Hashing embeddings only:** zero download, but not semantic; it would make the RAG quality
  comparison meaningless.
- **Hosted embeddings:** requires another free account and sends synthetic docs to a third party;
  local ONNX keeps the demo private and self-contained.

## Review trigger

Revisit if the eval shows retrieval quality is limited by the embedding model, if the corpus
becomes multilingual, or if an ONNX BGE-M3 runtime becomes a drop-in option.
