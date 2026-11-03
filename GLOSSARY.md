# Glossary

**Document** — A versioned Helios page with metadata and stable block IDs. A document belongs to one tenant and one version.

**Version** — A released edition of a document (`v1`, `v2`, `v3`) with `effective_from` and optional `superseded_at` dates.

**Block** — A stable unit of document content addressable by `block_id`, `page` and `anchor`. Citations resolve to blocks.

**Chunk** — One or more blocks prepared for retrieval. A chunk may span blocks, but every citation must resolve to a specific block.

**Citation** — A reference from a claim to a specific document version, page, block and anchor, with a short quote.

**Claim** — A user-visible assertion in an answer that must be supported by one or more citations.

**Answerability** — Whether the corpus contains enough evidence to answer. If not, the system must abstain rather than guess.

**Stale version** — A superseded document version that should not outrank the current version.

**Baseline** — The naive pipeline used for comparison: fixed-size chunks, dense-only retrieval, no version filter, no reranker, no abstention.

**Fixed pipeline** — The production-grade pipeline: structure-aware chunks, hybrid retrieval, version and tenant filters, reranking, claim-level citations and abstention.

**Tenant** — A fictional customer with isolated documents. The demo uses `northwind` and `acme`.

**Health report** — The evaluation summary page with metrics and failure examples.
