"""Load corpus manifests and generate the 80-question evaluation set.

The generator is deliberately deterministic and heuristic: it reads the
versioned manifest and builds questions from real blocks, headings and
version differences. It is not an LLM and needs no API key.

Quotas come from ``docs/eval-schema.md``:
24 single-hop, 16 multi-hop, 16 version-specific, 8 conflicting, 16 unanswerable.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from evals.schema import CATEGORIES, Category, GoldSource, Question, Split

DEFAULT_QUOTAS: dict[Category, int] = {
    "single_hop": 24,
    "multi_hop": 16,
    "version_specific": 16,
    "conflicting": 8,
    "unanswerable": 16,
}
DEFAULT_SEED = 20261103
DEFAULT_DATASET_PATH = Path("evals/data/questions.json")


class DatasetError(ValueError):
    """Raised when a manifest cannot satisfy the requested question quotas."""


class ManifestBlock(BaseModel):
    model_config = ConfigDict(extra="allow")

    block_id: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    heading: str = ""
    anchor: str = ""
    text: str


class ManifestDocument(BaseModel):
    model_config = ConfigDict(extra="allow")

    doc_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    doc_type: str = ""
    version: str = Field(min_length=1)
    effective_from: str | None = None
    superseded_at: str | None = None
    url_path: str | None = None
    blocks: list[ManifestBlock] = Field(default_factory=list)


class CorpusManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    generated_at: str | None = None
    product: str = "Helios"
    tenants: list[str] = Field(default_factory=list)
    versions: list[str] = Field(default_factory=list)
    documents: list[ManifestDocument] = Field(default_factory=list)
    failure_fixtures: dict[str, list[str]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Loading and writing
# ---------------------------------------------------------------------------


def _read_structured(path: Path) -> Any:
    suffix = path.suffix.lower()
    raw = path.read_text(encoding="utf-8")
    if suffix == ".json":
        return json.loads(raw)
    if suffix in {".yaml", ".yml"}:
        return yaml.safe_load(raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return yaml.safe_load(raw)


def load_manifest(path: str | Path) -> CorpusManifest:
    """Load and validate ``data/manifests/corpus.json`` (or a YAML equivalent)."""

    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"corpus manifest not found: {manifest_path}")
    data = _read_structured(manifest_path)
    if not isinstance(data, dict):
        raise DatasetError(f"manifest must be a JSON/YAML object: {manifest_path}")
    manifest = CorpusManifest.model_validate(data)
    if not manifest.documents:
        raise DatasetError(f"manifest has no documents: {manifest_path}")
    return manifest


def load_questions(path: str | Path) -> list[Question]:
    """Load a question set from JSON (array or ``{"questions": [...]}``) or JSONL."""

    question_path = Path(path)
    if not question_path.exists():
        raise FileNotFoundError(f"question dataset not found: {question_path}")
    raw = question_path.read_text(encoding="utf-8").strip()
    if not raw:
        raise DatasetError(f"question dataset is empty: {question_path}")
    if question_path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    else:
        data = json.loads(raw)
        rows = data.get("questions", []) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise DatasetError(f"question dataset must contain a list: {question_path}")
    questions = [Question.model_validate(row) for row in rows]
    _validate_unique_ids(questions)
    return questions


def save_questions(questions: Sequence[Question], path: str | Path) -> Path:
    """Write a deterministic JSON question set (array form)."""

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = [q.model_dump(mode="json", exclude_none=True) for q in questions]
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def _validate_unique_ids(questions: Sequence[Question]) -> None:
    ids = [q.question_id for q in questions]
    duplicates = sorted({qid for qid in ids if ids.count(qid) > 1})
    if duplicates:
        raise DatasetError(f"duplicate question_id values: {', '.join(duplicates)}")


def validate_quotas(
    questions: Sequence[Question],
    quotas: Mapping[Category, int] | None = None,
) -> None:
    """Raise if a question set does not match the requested category quotas."""

    expected = dict(quotas or DEFAULT_QUOTAS)
    counts = Counter(q.category for q in questions)
    mismatches = []
    for category in CATEGORIES:
        want = expected.get(category, 0)
        got = counts.get(category, 0)
        if got != want:
            mismatches.append(f"{category}: expected {want}, got {got}")
    if len(questions) != sum(expected.values()):
        mismatches.append(f"total: expected {sum(expected.values())}, got {len(questions)}")
    if mismatches:
        raise DatasetError("question quota mismatch: " + "; ".join(mismatches))
    _validate_unique_ids(questions)


def dataset_summary(questions: Sequence[Question]) -> dict[str, Any]:
    counts = Counter(q.category for q in questions)
    splits = Counter(q.split for q in questions)
    return {
        "total": len(questions),
        "by_category": {category: counts.get(category, 0) for category in CATEGORIES},
        "by_split": dict(sorted(splits.items())),
        "answerable": sum(1 for q in questions if q.answerable),
    }


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _BlockRef:
    doc: ManifestDocument
    block: ManifestBlock

    @property
    def tenant(self) -> str:
        return self.doc.tenant_id


_STOPWORDS = frozenset(
    """
    about above after again against all also among and any are because been before being
    below between both but can could did does doing down during each few for from further
    had has have having here how into its itself just more most not now off once only other
    our out over own same should some such than that the their them then there these they
    this those through to too under until up very was were what when where which while who
    why will with within would you your helios documentation page docs guide section block
    """.split()  # noqa: SIM905 - keep the word list readable
)
_WORD = re.compile(r"[a-z0-9][a-z0-9_-]{2,}")
_GENERIC_HEADINGS = frozenset(
    {"overview", "introduction", "summary", "overview and setup", "what's new", "whats new"}
)


def _version_key(version: str) -> tuple[tuple[int, ...], str]:
    return (tuple(int(part) for part in re.findall(r"\d+", version)), version)


def _sorted_docs(manifest: CorpusManifest) -> list[ManifestDocument]:
    return sorted(
        (doc for doc in manifest.documents if doc.blocks),
        key=lambda doc: (doc.tenant_id, doc.doc_id, _version_key(doc.version)),
    )


def _current_docs(manifest: CorpusManifest) -> list[ManifestDocument]:
    docs = _sorted_docs(manifest)
    current = [doc for doc in docs if doc.superseded_at is None]
    # A malformed manifest may mark several versions current; use the newest.
    # Tenant is part of the identity because doc_ids repeat across tenants.
    newest: dict[tuple[str, str], ManifestDocument] = {}
    for doc in current or docs:
        key = (doc.tenant_id, doc.doc_id)
        existing = newest.get(key)
        if existing is None or _version_key(doc.version) > _version_key(existing.version):
            newest[key] = doc
    return sorted(newest.values(), key=lambda doc: (doc.tenant_id, doc.doc_id))


def _tokens(text: str) -> set[str]:
    return {word for word in _WORD.findall(text.lower()) if word not in _STOPWORDS}


def _heading(ref: _BlockRef) -> str:
    heading = (ref.block.heading or "").strip().rstrip(":")
    if not heading or heading.lower() in _GENERIC_HEADINGS or heading.lower() == ref.doc.title.lower():
        return ""
    return heading


def _shorten(text: str, limit: int = 700) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(".,;:")
    return cut + "..."


def _round_robin_pools[T](
    pools: Mapping[tuple[str, str], list[T]],
    *,
    limit: int | None = None,
) -> list[T]:
    """Pick one item per tenant per round, then rotate documents.

    Tenant alternation matters because doc_ids repeat across Northwind and Acme;
    taking sorted keys directly would exhaust one tenant before reaching the other.
    """

    mutable = {key: list(value) for key, value in pools.items()}
    tenants = sorted({tenant for tenant, _doc_id in mutable})
    keys_by_tenant = {
        tenant: sorted(key for key in mutable if key[0] == tenant) for tenant in tenants
    }
    max_rounds = max((len(keys) for keys in keys_by_tenant.values()), default=0)
    selected: list[T] = []
    while True:
        progressed = False
        for rank in range(max_rounds):
            for tenant in tenants:
                keys = keys_by_tenant[tenant]
                if rank >= len(keys):
                    continue
                key = keys[rank]
                if mutable[key]:
                    selected.append(mutable[key].pop(0))
                    progressed = True
                    if limit is not None and len(selected) >= limit:
                        return selected
        if not progressed:
            return selected


def _round_robin(
    groups: Mapping[tuple[str, str], list[_BlockRef]],
    rng: random.Random,
) -> list[_BlockRef]:
    """Interleave blocks from different tenant/document pairs so a slice is not one page."""

    pools = {key: list(value) for key, value in sorted(groups.items())}
    for pool in pools.values():
        rng.shuffle(pool)
    return _round_robin_pools(pools)


def _tenant_doc_key(doc: ManifestDocument) -> tuple[str, str]:
    return (doc.tenant_id, doc.doc_id)


def _group_refs(refs: Iterable[_BlockRef]) -> dict[tuple[str, str], list[_BlockRef]]:
    groups: dict[tuple[str, str], list[_BlockRef]] = defaultdict(list)
    for ref in refs:
        groups[_tenant_doc_key(ref.doc)].append(ref)
    return dict(groups)


def _priority_doc_ids(manifest: CorpusManifest, fixture_name: str) -> set[str]:
    return {
        item.split("@", 1)[0]
        for item in manifest.failure_fixtures.get(fixture_name, [])
    }


def _select_single_hop(manifest: CorpusManifest, count: int, rng: random.Random) -> list[_BlockRef]:
    if count == 0:
        return []
    priority = _priority_doc_ids(manifest, "missed_detail")
    refs = [
        _BlockRef(doc, block)
        for doc in _current_docs(manifest)
        for block in doc.blocks
        if block.text.strip()
    ]
    refs.sort(
        key=lambda ref: (
            0 if ref.doc.doc_id in priority else 1,
            ref.doc.tenant_id,
            ref.doc.doc_id,
            ref.block.block_id,
        )
    )
    ordered = _round_robin(_group_refs(refs), rng)
    selected: list[_BlockRef] = []
    seen: set[tuple[str, str, str]] = set()
    for ref in ordered:
        content_key = (ref.doc.doc_id, ref.doc.version, ref.block.block_id)
        if content_key in seen:
            continue
        seen.add(content_key)
        selected.append(ref)
        if len(selected) == count:
            return selected
    raise DatasetError(
        f"single_hop needs {count} distinct current blocks, found {len(selected)}"
    )


def _best_block_pair(
    left: ManifestDocument, right: ManifestDocument
) -> tuple[ManifestBlock, ManifestBlock, float, set[str]]:
    best: tuple[ManifestBlock, ManifestBlock, float, set[str]] | None = None
    for block_a in sorted(left.blocks, key=lambda block: block.block_id):
        if not block_a.text.strip():
            continue
        for block_b in sorted(right.blocks, key=lambda block: block.block_id):
            if not block_b.text.strip():
                continue
            tokens_a = _tokens(block_a.text + " " + block_a.heading)
            tokens_b = _tokens(block_b.text + " " + block_b.heading)
            shared = tokens_a & tokens_b
            union = tokens_a | tokens_b
            score = (len(shared) / len(union)) if union else 0.0
            candidate = (block_a, block_b, score, shared)
            if best is None or (candidate[2], -len(block_a.text) - len(block_b.text)) > (
                best[2],
                -len(best[0].text) - len(best[1].text),
            ):
                best = candidate
    if best is None:
        raise DatasetError(f"no usable block pair in {left.doc_id}/{right.doc_id}")
    return best


def _select_multi_hop(
    manifest: CorpusManifest, count: int, rng: random.Random
) -> list[tuple[_BlockRef, _BlockRef, set[str]]]:
    if count == 0:
        return []
    current = _current_docs(manifest)
    by_tenant: dict[str, list[ManifestDocument]] = defaultdict(list)
    for doc in current:
        by_tenant[doc.tenant_id].append(doc)

    candidates: list[tuple[float, str, ManifestDocument, ManifestDocument, ManifestBlock, ManifestBlock, set[str]]] = []
    for tenant in sorted(by_tenant):
        docs = sorted(by_tenant[tenant], key=lambda doc: doc.doc_id)
        for index, left in enumerate(docs):
            for right in docs[index + 1 :]:
                block_a, block_b, score, shared = _best_block_pair(left, right)
                candidates.append((score, tenant, left, right, block_a, block_b, shared))

    if not candidates:
        raise DatasetError("multi_hop needs at least two current documents in one tenant")
    rng.shuffle(candidates)
    pools: dict[str, list[tuple[float, str, ManifestDocument, ManifestDocument, ManifestBlock, ManifestBlock, set[str]]]] = defaultdict(list)
    for candidate in candidates:
        pools[candidate[1]].append(candidate)
    for pool in pools.values():
        pool.sort(key=lambda item: -item[0])

    selected: list[tuple[_BlockRef, _BlockRef, set[str]]] = []
    selected_pairs: set[tuple[str, str, str]] = set()
    selected_content: set[tuple[str, str, str, str]] = set()
    cursors: Counter[str] = Counter()
    while len(selected) < count:
        progressed = False
        for tenant in sorted(pools):
            pool = pools[tenant]
            while cursors[tenant] < len(pool):
                _score, _tenant, left, right, block_a, block_b, shared = pool[cursors[tenant]]
                cursors[tenant] += 1
                pair_key = (tenant, left.doc_id, right.doc_id)
                if pair_key in selected_pairs:
                    continue
                content_key = (left.doc_id, block_a.block_id, right.doc_id, block_b.block_id)
                if content_key in selected_content:
                    continue
                selected.append((_BlockRef(left, block_a), _BlockRef(right, block_b), shared))
                selected_pairs.add(pair_key)
                selected_content.add(content_key)
                progressed = True
                break
            if len(selected) == count:
                return selected
        if not progressed:
            break
    raise DatasetError(f"multi_hop needs {count} document pairs, found {len(selected)}")


def _select_version_specific(
    manifest: CorpusManifest, count: int, rng: random.Random
) -> list[tuple[_BlockRef, list[str]]]:
    if count == 0:
        return []
    by_doc: dict[tuple[str, str], list[ManifestDocument]] = defaultdict(list)
    for doc in _sorted_docs(manifest):
        by_doc[_tenant_doc_key(doc)].append(doc)

    priority = _priority_doc_ids(manifest, "stale_version")
    candidates: list[tuple[int, _BlockRef, list[str]]] = []
    for (tenant_id, doc_id), versions in sorted(by_doc.items()):
        current_candidates = [doc for doc in versions if doc.superseded_at is None]
        current = max(current_candidates or versions, key=lambda doc: _version_key(doc.version))
        superseded = sorted(
            {doc.version for doc in versions if doc.version != current.version},
            key=_version_key,
        )
        if not superseded:
            continue
        for block in sorted(current.blocks, key=lambda item: item.block_id):
            if block.text.strip():
                candidates.append(
                    (0 if doc_id in priority else 1, _BlockRef(current, block), superseded)
                )
    candidates.sort(
        key=lambda item: (
            item[0],
            item[1].doc.tenant_id,
            item[1].doc.doc_id,
            item[1].block.block_id,
        )
    )

    groups: dict[tuple[str, str], list[tuple[_BlockRef, list[str]]]] = defaultdict(list)
    for _priority, ref, superseded in candidates:
        groups[_tenant_doc_key(ref.doc)].append((ref, superseded))
    pools = {key: list(value) for key, value in sorted(groups.items())}
    for pool in pools.values():
        rng.shuffle(pool)
    selected: list[tuple[_BlockRef, list[str]]] = []
    seen: set[tuple[str, str, str]] = set()
    for ref, superseded in _round_robin_pools(pools):
        content_key = (ref.doc.doc_id, ref.doc.version, ref.block.block_id)
        if content_key in seen:
            continue
        seen.add(content_key)
        selected.append((ref, superseded))
        if len(selected) == count:
            return selected
    raise DatasetError(
        f"version_specific needs {count} current blocks from versioned docs, "
        f"found {len(selected)}"
    )


def _conflict_groups(manifest: CorpusManifest) -> list[tuple[str, list[tuple[ManifestDocument, ManifestBlock]]]]:
    by_doc: dict[tuple[str, str], list[ManifestDocument]] = defaultdict(list)
    for doc in _sorted_docs(manifest):
        by_doc[_tenant_doc_key(doc)].append(doc)

    groups: list[tuple[str, list[tuple[ManifestDocument, ManifestBlock]]]] = []
    for doc_key in sorted(by_doc):
        docs = by_doc[doc_key]
        by_key: dict[str, list[tuple[ManifestDocument, ManifestBlock]]] = defaultdict(list)
        for doc in docs:
            for block in doc.blocks:
                if block.text.strip():
                    key = block.block_id or (block.heading or doc.title)
                    by_key[key].append((doc, block))
        for key, entries in sorted(by_key.items()):
            by_version = {}
            for doc, block in entries:
                by_version.setdefault(doc.version, (doc, block))
            if len(by_version) < 2:
                continue
            if len({" ".join(block.text.split()) for _doc, block in by_version.values()}) < 2:
                continue
            ordered = sorted(by_version.values(), key=lambda item: _version_key(item[0].version))
            groups.append((key, ordered))
    return groups


def _select_conflicting(
    manifest: CorpusManifest, count: int, rng: random.Random
) -> list[tuple[str, list[tuple[ManifestDocument, ManifestBlock]]]]:
    if count == 0:
        return []
    priority = _priority_doc_ids(manifest, "conflicting_versions")
    groups = _conflict_groups(manifest)
    groups.sort(
        key=lambda item: (
            0 if item[1][0][0].doc_id in priority else 1,
            item[1][0][0].tenant_id,
            item[1][0][0].doc_id,
            item[0],
        )
    )
    by_doc: dict[
        tuple[str, str],
        list[tuple[str, list[tuple[ManifestDocument, ManifestBlock]]]],
    ] = defaultdict(list)
    for group in groups:
        by_doc[_tenant_doc_key(group[1][0][0])].append(group)
    pools = {key: list(value) for key, value in sorted(by_doc.items())}
    for pool in pools.values():
        rng.shuffle(pool)
    selected: list[tuple[str, list[tuple[ManifestDocument, ManifestBlock]]]] = []
    seen: set[tuple[str, str]] = set()
    for match_key, entries in _round_robin_pools(pools):
        content_key = (entries[0][0].doc_id, match_key)
        if content_key in seen:
            continue
        seen.add(content_key)
        selected.append((match_key, entries))
        if len(selected) == count:
            return selected
    raise DatasetError(
        f"conflicting needs {count} groups of differing versions, found {len(selected)}"
    )


# Distinctive terms that are absent from a synthetic Helios corpus. A candidate
# is only used when none of its terms occurs anywhere in the manifest.
_UNANSWERABLE_CANDIDATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("What is the SLA for an air-gapped Helios installation?", ("air-gapped",)),
    ("How do I export Helios audit logs to Splunk?", ("splunk",)),
    ("How do I configure SCIM provisioning with Okta?", ("okta", "scim")),
    ("Does Helios support SAML single sign-on with Ping Identity?", ("ping identity",)),
    ("Where can I download the Helios SOC 2 Type II report?", ("soc 2", "soc2")),
    ("What is the HIPAA business associate agreement process?", ("hipaa",)),
    ("Which Helios regions are certified under ISO 27001?", ("iso 27001", "iso27001")),
    ("How long does Helios retain data in the Australia region?", ("australia",)),
    ("How do I configure Helios to use an Oracle database?", ("oracle",)),
    ("Does Helios provide a native SAP integration?", ("sap",)),
    ("How do I sync Helios projects with Jira?", ("jira",)),
    ("Can Helios post release notifications to Microsoft Teams?", ("microsoft teams",)),
    ("How do I connect a ServiceNow incident queue to Helios?", ("servicenow", "service now")),
    ("What is the SMTP relay hostname for Helios email notifications?", ("smtp relay",)),
    ("Does the Helios API support GraphQL subscriptions?", ("graphql",)),
    ("How do I stream Helios events over Kafka?", ("kafka",)),
    ("Which RabbitMQ exchange does Helios publish to?", ("rabbitmq",)),
    ("How do I configure a Redis cache for Helios sessions?", ("redis",)),
    ("What is the maximum Snowflake warehouse size Helios supports?", ("snowflake",)),
    ("How do I load Helios data into Google BigQuery?", ("bigquery", "big query")),
    ("Does Helios have a native Android offline mode?", ("android", "offline mode")),
    ("Is there a Helios Chrome extension for quick capture?", ("chrome extension",)),
    ("How do I install the Helios Outlook add-in?", ("outlook add-in", "outlook addin")),
    ("What is the Shopify connector setup process?", ("shopify",)),
    ("Can Helios charge annual subscriptions through Stripe?", ("stripe",)),
    ("Does Helios accept cryptocurrency payments?", ("cryptocurrency", "bitcoin", "ethereum")),
    ("What is the student discount for Helios?", ("student discount",)),
    ("Is there a lifetime license option for Helios?", ("lifetime license", "perpetual license")),
    ("How do I enable bring-your-own-key encryption with an HSM?", ("hsm", "bring-your-own-key")),
    ("What is the source code escrow policy for Helios?", ("source code escrow", "escrow")),
    ("Does Helios offer a white-label version for agencies?", ("white-label", "white label")),
    ("How do I configure a custom TLS certificate for my Helios domain?", ("custom tls", "tls certificate")),
    ("Which GPU does Helios use to train its recommendation model?", ("gpu",)),
    ("How do I migrate a Helios workspace to a blockchain-based audit trail?", ("blockchain",)),
    ("What is the Helios policy for employee personal devices in Brazil?", ("brazil",)),
    ("How do I set up an IMAP mailbox for Helios support?", ("imap",)),
    ("Does Helios provide a Zendesk side conversation integration?", ("zendesk",)),
    ("What is the data processing addendum for Swiss customers?", ("swiss", "switzerland")),
    ("How do I request a physical backup tape for Helios?", ("backup tape", "physical backup")),
    ("Which quantum-safe cipher suites does Helios support?", ("quantum",)),
)

_FICTIONAL_FEATURES: tuple[str, ...] = (
    "teleport",
    "holodeck",
    "warp-drive",
    "dark-mode-scheduler",
    "offline-satellite-sync",
    "quantum-export",
    "holographic-audit",
    "time-travel-rollback",
)


def _cross_tenant_candidates(
    manifest: CorpusManifest,
) -> list[tuple[str, tuple[str, ...], str]]:
    """Ask one tenant about another tenant's private page.

    The question is unanswerable under the tenant filter, which exercises the
    cross-tenant leak failure mode without putting private content in the
    question or gold answer.
    """

    by_tenant: dict[str, list[ManifestDocument]] = defaultdict(list)
    for doc in _current_docs(manifest):
        by_tenant[doc.tenant_id].append(doc)
    tenants = sorted(by_tenant)
    if len(tenants) < 2:
        return []

    candidates: list[tuple[str, tuple[str, ...], str]] = []
    for tenant in tenants:
        for other in tenants:
            if other == tenant:
                continue
            private_docs = [
                doc
                for doc in by_tenant[other]
                if "private" in doc.doc_id.lower()
                or "private" in doc.title.lower()
                or any("confidential" in block.text.lower() for block in doc.blocks)
            ]
            if not private_docs:
                continue
            doc = private_docs[0]
            usable_blocks = [
                block
                for block in doc.blocks
                if block.heading and "confidential" not in block.heading.lower()
            ] or doc.blocks
            if not usable_blocks:
                continue
            block = usable_blocks[0]
            owner_label = "" if other.lower() in doc.title.lower() else f"{other.title()} "
            question = (
                f"What does the {owner_label}{doc.title} say about {block.heading.lower()}?"
            )
            candidates.append((question, ("cross-tenant", other), tenant))
            break
    return candidates


def _select_unanswerable(
    manifest: CorpusManifest, count: int, rng: random.Random
) -> list[tuple[str, tuple[str, ...], str | None]]:
    if count == 0:
        return []
    corpus_text = " ".join(
        [
            manifest.product,
            *manifest.tenants,
            *manifest.versions,
            *(
                " ".join(
                    [
                        doc.doc_id,
                        doc.title,
                        *(
                            f"{block.heading} {block.anchor} {block.text}"
                            for block in doc.blocks
                        ),
                    ]
                )
                for doc in manifest.documents
            ),
        ]
    ).lower()
    cross_tenant = _cross_tenant_candidates(manifest)
    selected: list[tuple[str, tuple[str, ...], str | None]] = [
        (question, terms, tenant) for question, terms, tenant in cross_tenant[:count]
    ]
    candidates = list(_UNANSWERABLE_CANDIDATES)
    rng.shuffle(candidates)
    generic = [
        (question, terms, None)
        for question, terms in candidates
        if not any(term.lower() in corpus_text for term in terms)
    ]
    if len(selected) + len(generic) < count:
        for feature in _FICTIONAL_FEATURES:
            if feature not in corpus_text:
                generic.append(
                    (
                        f"How do I enable the Helios {feature.replace('-', ' ')} feature?",
                        (feature,),
                        None,
                    )
                )
    for candidate in generic:
        if len(selected) >= count:
            break
        selected.append(candidate)
    if len(selected) < count:
        raise DatasetError(f"unanswerable needs {count} absent-topic questions, found {len(selected)}")
    rng.shuffle(selected)
    return selected[:count]


def _single_hop_question(ref: _BlockRef, index: int) -> Question:
    heading = _heading(ref)
    title = ref.doc.title
    if heading:
        templates = (
            "What does the {title} documentation say about {heading}?",
            "According to the {title} page, what should I know about {heading}?",
            "How does {title} describe {heading}?",
            "What guidance does {title} give on {heading}?",
        )
        question = templates[index % len(templates)].format(title=title, heading=heading.lower())
    else:
        templates = (
            "What does the {title} documentation cover?",
            "What should I know about the {title} page?",
            "Which guidance does the {title} documentation provide?",
        )
        question = templates[index % len(templates)].format(title=title)
    return Question(
        question_id=f"single-hop-{index + 1:03d}",
        tenant_id=ref.tenant,
        question=question,
        category="single_hop",
        answerable=True,
        gold_answer=_shorten(ref.block.text),
        gold_sources=[
            GoldSource(
                doc_id=ref.doc.doc_id,
                version=ref.doc.version,
                block_id=ref.block.block_id,
                page=ref.block.page,
                anchor=ref.block.anchor or None,
                title=ref.doc.title,
                quote=_shorten(ref.block.text),
            )
        ],
        notes=(
            f"Generated from {ref.doc.doc_id}@{ref.doc.version} block "
            f"{ref.block.block_id}; answerable from one page."
        ),
    )


def _multi_hop_question(
    left: _BlockRef,
    right: _BlockRef,
    shared: set[str],
    index: int,
) -> Question:
    heading_left = _heading(left)
    heading_right = _heading(right)
    if heading_left and heading_right:
        question = (
            f"Compare how {left.doc.title} handles {heading_left.lower()} with how "
            f"{right.doc.title} handles {heading_right.lower()}."
        )
    elif heading_left:
        question = (
            f"Compare the guidance on {heading_left.lower()} in {left.doc.title} with "
            f"the guidance in {right.doc.title}."
        )
    elif heading_right:
        question = (
            f"Compare the guidance in {left.doc.title} with the guidance on "
            f"{heading_right.lower()} in {right.doc.title}."
        )
    else:
        question = f"Compare the guidance in {left.doc.title} with the guidance in {right.doc.title}."
    shared_note = f" Shared terms: {', '.join(sorted(shared))}." if shared else ""
    gold_answer = (
        f"{left.doc.title} ({left.doc.version}) says: {_shorten(left.block.text)} "
        f"{right.doc.title} ({right.doc.version}) says: {_shorten(right.block.text)}"
    )
    return Question(
        question_id=f"multi-hop-{index + 1:03d}",
        tenant_id=left.tenant,
        question=question,
        category="multi_hop",
        answerable=True,
        gold_answer=gold_answer,
        gold_sources=[
            GoldSource(
                doc_id=ref.doc.doc_id,
                version=ref.doc.version,
                block_id=ref.block.block_id,
                page=ref.block.page,
                anchor=ref.block.anchor or None,
                title=ref.doc.title,
                quote=_shorten(ref.block.text),
            )
            for ref in (left, right)
        ],
        notes=(
            "Requires both pages; partial retrieval gets partial recall but fails "
            f"all-gold@10.{shared_note}"
        ),
    )


def _version_specific_question(
    ref: _BlockRef,
    superseded: list[str],
    index: int,
) -> Question:
    heading = _heading(ref)
    title = ref.doc.title
    if heading:
        templates = (
            "In {version}, what does the {title} documentation say about {heading}?",
            "In {version}, how does {title} handle {heading}?",
            "For {version} specifically, what is the guidance in {title} on {heading}?",
        )
        question = templates[index % len(templates)].format(
            version=ref.doc.version,
            title=title,
            heading=heading.lower(),
        )
    else:
        question = f"In {ref.doc.version}, what does the {title} documentation cover?"
    return Question(
        question_id=f"version-specific-{index + 1:03d}",
        tenant_id=ref.tenant,
        question=question,
        category="version_specific",
        answerable=True,
        gold_answer=_shorten(ref.block.text),
        gold_sources=[
            GoldSource(
                doc_id=ref.doc.doc_id,
                version=ref.doc.version,
                block_id=ref.block.block_id,
                page=ref.block.page,
                anchor=ref.block.anchor or None,
                title=ref.doc.title,
                quote=_shorten(ref.block.text),
            )
        ],
        notes=(
            f"Version-specific: target {ref.doc.version}; superseded versions "
            f"{', '.join(superseded) or 'none'}."
        ),
        target_version=ref.doc.version,
        superseded_versions=superseded,
    )


def _conflicting_question(
    match_key: str,
    entries: list[tuple[ManifestDocument, ManifestBlock]],
    index: int,
) -> Question:
    doc = entries[0][0]
    heading = ""
    for candidate_doc, candidate_block in entries:
        probe = _BlockRef(candidate_doc, candidate_block)
        heading = _heading(probe)
        if heading:
            break
    topic = heading.lower() if heading else doc.title.lower()
    templates = (
        "What does Helios say about {topic}?",
        "What is the guidance on {topic} in Helios?",
        "How should I handle {topic} in Helios?",
    )
    question = templates[index % len(templates)].format(topic=topic)
    versions = [candidate_doc.version for candidate_doc, _block in entries]
    gold_answer = "Versions disagree. " + " ".join(
        f"{candidate_doc.version} says: {_shorten(candidate_block.text)}"
        for candidate_doc, candidate_block in entries
    )
    latest = max(versions, key=_version_key)
    superseded = sorted({version for version in versions if version != latest}, key=_version_key)
    return Question(
        question_id=f"conflicting-{index + 1:03d}",
        tenant_id=doc.tenant_id,
        question=question,
        category="conflicting",
        answerable=True,
        gold_answer=gold_answer,
        gold_sources=[
            GoldSource(
                doc_id=candidate_doc.doc_id,
                version=candidate_doc.version,
                block_id=candidate_block.block_id,
                page=candidate_block.page,
                anchor=candidate_block.anchor or None,
                title=candidate_doc.title,
                quote=_shorten(candidate_block.text),
            )
            for candidate_doc, candidate_block in entries
        ],
        notes=(
            f"Underspecified: {match_key} differs across "
            f"{', '.join(versions)}; a correct answer states the versions or asks which one."
        ),
        superseded_versions=superseded,
        failure_mode="conflicting_versions",
    )


def _unanswerable_question(
    question_text: str,
    terms: tuple[str, ...],
    tenant_id: str,
    index: int,
) -> Question:
    return Question(
        question_id=f"unanswerable-{index + 1:03d}",
        tenant_id=tenant_id,
        question=question_text,
        category="unanswerable",
        answerable=False,
        gold_answer=(
            "The corpus does not contain enough evidence to answer this question; "
            "the correct behavior is to abstain."
        ),
        gold_sources=[],
        notes=f"No gold source; absent-topic guard terms: {', '.join(terms)}.",
    )


def generate_questions(
    manifest: CorpusManifest,
    *,
    quotas: Mapping[Category, int] | None = None,
    seed: int = DEFAULT_SEED,
) -> list[Question]:
    """Generate a deterministic question set from a validated corpus manifest.

    The default quotas produce exactly 80 questions split 40 dev / 40 test.
    Raises :class:`DatasetError` when the manifest lacks enough material.
    """

    requested = {category: int((quotas or DEFAULT_QUOTAS).get(category, 0)) for category in CATEGORIES}
    total = sum(requested.values())
    if total <= 0:
        raise DatasetError("at least one question must be requested")
    rng = random.Random(seed)

    by_category: dict[Category, list[Question]] = {}

    single_refs = _select_single_hop(manifest, requested["single_hop"], rng)
    by_category["single_hop"] = [
        _single_hop_question(ref, index) for index, ref in enumerate(single_refs)
    ]

    multi_refs = _select_multi_hop(manifest, requested["multi_hop"], rng)
    by_category["multi_hop"] = [
        _multi_hop_question(left, right, shared, index)
        for index, (left, right, shared) in enumerate(multi_refs)
    ]

    version_refs = _select_version_specific(manifest, requested["version_specific"], rng)
    by_category["version_specific"] = [
        _version_specific_question(ref, superseded, index)
        for index, (ref, superseded) in enumerate(version_refs)
    ]

    conflict_refs = _select_conflicting(manifest, requested["conflicting"], rng)
    by_category["conflicting"] = [
        _conflicting_question(match_key, entries, index)
        for index, (match_key, entries) in enumerate(conflict_refs)
    ]

    tenants = manifest.tenants or sorted({doc.tenant_id for doc in manifest.documents})
    tenants = tenants or ["northwind"]
    unanswered = _select_unanswerable(manifest, requested["unanswerable"], rng)
    by_category["unanswerable"] = [
        _unanswerable_question(
            text,
            terms,
            tenant or tenants[index % len(tenants)],
            index,
        )
        for index, (text, terms, tenant) in enumerate(unanswered)
    ]

    # Stratify the dev/test split inside each category. Default quotas are even,
    # so this yields exactly 40 dev and 40 test questions.
    for category in CATEGORIES:
        questions = by_category[category]
        order = list(range(len(questions)))
        rng.shuffle(order)
        half = len(questions) // 2
        for position, original_index in enumerate(order):
            split: Split = "dev" if position < half else "test"
            questions[original_index] = questions[original_index].model_copy(
                update={"split": split}
            )

    ordered: list[Question] = []
    for category in CATEGORIES:
        ordered.extend(by_category[category])
    final: list[Question] = []
    for index, question in enumerate(ordered, start=1):
        final.append(question.model_copy(update={"question_id": f"q{index:03d}"}))
    validate_quotas(final, requested)
    return final


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the Forge evaluation question set from a corpus manifest."
    )
    parser.add_argument(
        "--manifest",
        default="data/manifests/corpus.json",
        help="corpus manifest path (default: data/manifests/corpus.json)",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_DATASET_PATH),
        help=f"output question JSON (default: {DEFAULT_DATASET_PATH})",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)
    questions = generate_questions(manifest, seed=args.seed)
    validate_quotas(questions)
    out = save_questions(questions, args.out)
    summary = dataset_summary(questions)
    print(f"wrote {summary['total']} questions to {out}")
    print(f"  categories: {summary['by_category']}")
    print(f"  splits: {summary['by_split']}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
