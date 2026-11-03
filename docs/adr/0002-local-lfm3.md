# 0002 — Local LFM3-1.7B for fast evaluation loops

**Status:** accepted  
**Date:** 2026-11-04

## Context

The first real RAG evaluation used the OrcaRouter free tier. It works with
`reasoning_effort="none"`, but the free tier is slow and variable: one baseline
question timed out at 180 seconds, and a full 80-question × 2-pipeline run would
take roughly an hour. The laptop also has a local LFM3-1.7B chat service
(`lfm3 chat`) on an OpenAI-compatible endpoint, with 32K context and about
43 tokens/second on the GTX 1050 Ti.

## Decision

Add a first-class `lfm3` provider (`http://127.0.0.1:8080/v1`, model
`lfm3-1.7b`) and use it for fast test/refinement loops. Keep OrcaRouter as the
hosted cross-check and the final public-demo provider.

- The local service is started with `lfm3 chat` and stopped with `lfm3 off`.
- `LFM3_BASE_URL` and `LFM3_MODEL` configure the endpoint.
- The provider uses the same OpenAI-compatible transport and JSON mode as the
  hosted providers; no API key is required.
- The local model has thinking disabled by the wrapper; if it emits a stray
  `</think>`, the existing JSON parser ignores text outside the object.

## Consequences

- No API cost or rate-limit waits for iteration.
- The 1.7B model is weaker than the hosted free models and is explicitly not
  recommended for complex multi-step reasoning. Its failures are useful for
  prompt and retrieval refinement, but not for headline quality claims.
- The GPU is shared with the desktop; only one model may be loaded at a time.
- The public demo should use the hosted provider or a recorded local run; a
  laptop-local service is not a reliable public endpoint.

## Alternatives considered

- **OrcaRouter only:** simpler, but slow and rate-limited for repeated runs.
- **Ollama Qwen 3.5 4B:** also local, but a separate runtime and model download;
  LFM3 is already installed and benchmarked.
- **Paid frontier API:** best quality, but violates the strict $0 constraint.

## Review trigger

Revisit if the local model cannot follow the citation schema reliably after
prompt refinement, or if the eval needs a stronger model for the headline run.
