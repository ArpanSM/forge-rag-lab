"""Vector store abstractions.

``InMemoryVectorStore`` is used by tests and offline development.
``QdrantVectorStore`` imports ``qdrant-client`` only when a client is needed.
"""

from __future__ import annotations

import logging
import math
import uuid
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from rag.models import RetrievedBlock

logger = logging.getLogger(__name__)


@runtime_checkable
class VectorStore(Protocol):
    name: str

    def upsert(
        self, blocks: Sequence[RetrievedBlock], vectors: Sequence[Sequence[float]]
    ) -> None: ...

    def search(
        self,
        query_vector: Sequence[float],
        *,
        tenant_id: str,
        top_k: int = 10,
        current_only: bool = False,
        versions: set[str] | None = None,
    ) -> list[RetrievedBlock]: ...

    def count(self) -> int: ...

    def status(self) -> str: ...

    def clear(self) -> None: ...


class InMemoryVectorStore:
    """Cosine-similarity store with payload filters, for tests and local dev."""

    name = "in-memory"

    def __init__(self, dimension: int | None = None) -> None:
        self.dimension = dimension
        self._items: dict[str, tuple[RetrievedBlock, list[float], float]] = {}

    def upsert(self, blocks: Sequence[RetrievedBlock], vectors: Sequence[Sequence[float]]) -> None:
        if len(blocks) != len(vectors):
            raise ValueError("blocks and vectors must have the same length")
        for block, vector in zip(blocks, vectors, strict=True):
            values = [float(value) for value in vector]
            if self.dimension is None:
                self.dimension = len(values)
            if len(values) != self.dimension:
                raise ValueError(
                    f"vector dimension {len(values)} does not match store dimension "
                    f"{self.dimension}"
                )
            norm = math.sqrt(sum(value * value for value in values))
            self._items[block.chunk_ref] = (block.model_copy(), values, norm)

    def search(
        self,
        query_vector: Sequence[float],
        *,
        tenant_id: str,
        top_k: int = 10,
        current_only: bool = False,
        versions: set[str] | None = None,
    ) -> list[RetrievedBlock]:
        if top_k <= 0 or not tenant_id or not self._items:
            return []
        query = [float(value) for value in query_vector]
        query_norm = math.sqrt(sum(value * value for value in query))
        if query_norm == 0.0:
            return []

        scored: list[tuple[float, RetrievedBlock]] = []
        for block, vector, norm in self._items.values():
            if not _passes_filters(
                block, tenant_id=tenant_id, current_only=current_only, versions=versions
            ):
                continue
            if len(vector) != len(query) or norm == 0.0:
                continue
            similarity = sum(left * right for left, right in zip(vector, query, strict=True))
            scored.append((similarity / (norm * query_norm), block))

        scored.sort(key=lambda item: (-item[0], item[1].chunk_ref))
        return [
            block.model_copy(
                update={
                    "score": score,
                    "dense_score": score,
                    "retrieval_source": "dense",
                }
            )
            for score, block in scored[:top_k]
        ]

    def count(self) -> int:
        return len(self._items)

    def status(self) -> str:
        return "ok"

    def clear(self) -> None:
        self._items.clear()


class QdrantVectorStore:
    """Qdrant-backed store with tenant and current-version payload filters."""

    name = "qdrant"

    def __init__(
        self,
        *,
        url: str = "http://localhost:6333",
        api_key: str | None = None,
        collection: str = "helios_blocks",
        dimension: int = 1024,
        prefer_grpc: bool = False,
        client: object | None = None,
    ) -> None:
        self.url = url
        self.api_key = api_key
        self.collection = collection
        self.dimension = dimension
        self.prefer_grpc = prefer_grpc
        self._client_instance = client
        self._collection_ready = False

    @property
    def _client(self):
        if self._client_instance is None:
            try:
                from qdrant_client import QdrantClient
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "qdrant-client is not installed; install the retrieval extras "
                    "or set VECTOR_STORE=memory"
                ) from exc
            self._client_instance = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                prefer_grpc=self.prefer_grpc,
            )
        return self._client_instance

    def _ensure_collection(self) -> None:
        if self._collection_ready:
            return
        from qdrant_client import models

        client = self._client
        exists = False
        if hasattr(client, "collection_exists"):
            exists = bool(client.collection_exists(self.collection))
        else:  # pragma: no cover - old qdrant-client
            collections = client.get_collections().collections
            exists = any(item.name == self.collection for item in collections)
        if not exists:
            client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(
                    size=self.dimension,
                    distance=models.Distance.COSINE,
                ),
            )
            for field_name, schema in (
                ("tenant_id", models.PayloadSchemaType.KEYWORD),
                ("version", models.PayloadSchemaType.KEYWORD),
                ("doc_id", models.PayloadSchemaType.KEYWORD),
                ("is_current", models.PayloadSchemaType.BOOL),
            ):
                try:
                    client.create_payload_index(
                        collection_name=self.collection,
                        field_name=field_name,
                        field_schema=schema,
                    )
                except Exception as exc:  # noqa: BLE001  # pragma: no cover - index exists
                    logger.debug("payload index %s was not created: %s", field_name, exc)
        self._collection_ready = True

    def _build_filter(self, *, tenant_id: str, current_only: bool, versions: set[str] | None):
        from qdrant_client import models

        conditions = [
            models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id))
        ]
        if current_only:
            conditions.append(
                models.FieldCondition(key="is_current", match=models.MatchValue(value=True))
            )
        if versions:
            conditions.append(
                models.FieldCondition(
                    key="version",
                    match=models.MatchAny(any=sorted(versions)),
                )
            )
        return models.Filter(must=conditions)

    def upsert(self, blocks: Sequence[RetrievedBlock], vectors: Sequence[Sequence[float]]) -> None:
        from qdrant_client import models

        if len(blocks) != len(vectors):
            raise ValueError("blocks and vectors must have the same length")
        if not blocks:
            return
        self._ensure_collection()
        points = [
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, block.chunk_ref)),
                vector=[float(value) for value in vector],
                payload=block.model_dump(mode="json"),
            )
            for block, vector in zip(blocks, vectors, strict=True)
        ]
        for start in range(0, len(points), 128):
            self._client.upsert(
                collection_name=self.collection,
                points=points[start : start + 128],
            )

    def search(
        self,
        query_vector: Sequence[float],
        *,
        tenant_id: str,
        top_k: int = 10,
        current_only: bool = False,
        versions: set[str] | None = None,
    ) -> list[RetrievedBlock]:
        if top_k <= 0 or not tenant_id:
            return []
        self._ensure_collection()
        query_filter = self._build_filter(
            tenant_id=tenant_id, current_only=current_only, versions=versions
        )
        client = self._client
        if hasattr(client, "query_points"):
            response = client.query_points(
                collection_name=self.collection,
                query=[float(value) for value in query_vector],
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )
            points = response.points
        else:  # pragma: no cover - old qdrant-client
            points = client.search(
                collection_name=self.collection,
                query_vector=[float(value) for value in query_vector],
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )

        results: list[RetrievedBlock] = []
        for point in points:
            payload = dict(point.payload or {})
            payload.update(
                {
                    "score": float(point.score),
                    "dense_score": float(point.score),
                    "retrieval_source": "dense",
                }
            )
            results.append(RetrievedBlock.model_validate(payload))
        return results

    def count(self) -> int:
        self._ensure_collection()
        return int(self._client.count(collection_name=self.collection, exact=True).count)

    def status(self) -> str:
        try:
            self._client.get_collections()
            return "ok"
        except Exception:  # noqa: BLE001 - health endpoint reports unavailability
            return "unavailable"

    def clear(self) -> None:
        from qdrant_client import models

        try:
            self._client.delete_collection(self.collection)
        except Exception:  # noqa: BLE001 - clearing is best effort
            return
        self._collection_ready = False
        self._client.create_collection(
            collection_name=self.collection,
            vectors_config=models.VectorParams(
                size=self.dimension,
                distance=models.Distance.COSINE,
            ),
        )


def _passes_filters(
    block: RetrievedBlock,
    *,
    tenant_id: str,
    current_only: bool,
    versions: set[str] | None,
) -> bool:
    if block.tenant_id != tenant_id:
        return False
    if current_only and not block.is_current:
        return False
    if versions is not None:
        return block.version in versions
    return True
