from collections.abc import Sequence
from http import HTTPStatus
from uuid import UUID

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from src.application.search.models import ArticleHits, ChunkHit, SearchChunk, SearchScope

from .config import QdrantConfig

DENSE_VECTOR = "dense"
BM25_VECTOR = "bm25"
BM25_MODEL = "qdrant/bm25"

_UPSERT_BATCH_SIZE = 64
_PREFETCH_FACTOR = 5
_HIT_PAYLOAD = ["article_id", "revision_id", "text", "heading_path", "anchor"]


class QdrantSearchChunkRepository:
    """
    Фрагменты в Qdrant: dense-вектор (эмбеддинг) + sparse BM25, вычисляемый на сервере Qdrant.

    Поиск — гибридный (RRF двух prefetch), всегда с фильтром области доступа.
    """

    def __init__(self, client: AsyncQdrantClient, config: QdrantConfig) -> None:
        self._client = client
        self._config = config
        self._collection = config.collection_name

    @property
    def index_name(self) -> str:
        return self._collection

    def _bm25_document(self, text: str) -> models.Document:
        # tokenizer по умолчанию ("word"): с "multilingual" русский стемминг не применяется
        return models.Document(text=text, model=BM25_MODEL, options={"language": self._config.bm25_language})

    async def ensure_collection(self, dense_size: int) -> None:
        """Создаёт коллекцию текущего поколения и payload-индексы, если их ещё нет."""

        if await self._client.collection_exists(self._collection):
            return

        try:
            await self._client.create_collection(
                self._collection,
                vectors_config={
                    DENSE_VECTOR: models.VectorParams(size=dense_size, distance=models.Distance.COSINE)
                },
                sparse_vectors_config={BM25_VECTOR: models.SparseVectorParams(modifier=models.Modifier.IDF)},
            )
        except UnexpectedResponse as exc:
            # Коллекцию параллельно создал другой процесс (API или worker); индексы ниже идемпотентны
            if exc.status_code != HTTPStatus.CONFLICT:
                raise
        await self._client.create_payload_index(
            self._collection,
            "organization_id",
            models.KeywordIndexParams(type=models.KeywordIndexType.KEYWORD, is_tenant=True),
        )
        for field in ("space_id", "article_id", "revision_id"):
            await self._client.create_payload_index(self._collection, field, models.PayloadSchemaType.KEYWORD)

    def _to_point(self, chunk: SearchChunk) -> models.PointStruct:
        return models.PointStruct(
            id=str(chunk.id),
            vector={
                DENSE_VECTOR: list(chunk.dense_vector),
                BM25_VECTOR: self._bm25_document(chunk.search_text),
            },
            payload={
                "organization_id": str(chunk.organization_id),
                "space_id": str(chunk.space_id),
                "article_id": str(chunk.article_id),
                "revision_id": str(chunk.revision_id),
                "position": chunk.position,
                "heading_path": list(chunk.heading_path),
                "anchor": chunk.anchor,
                "text": chunk.text,
                "content_hash": chunk.content_hash,
                "media_ids": [str(media_id) for media_id in chunk.media_ids],
            },
        )

    @staticmethod
    def _article_filter(article_id: UUID) -> models.Filter:
        return models.Filter(
            must=[models.FieldCondition(key="article_id", match=models.MatchValue(value=str(article_id)))],
        )

    async def replace_article_chunks(
        self,
        article_id: UUID,
        revision_id: UUID,
        chunks: Sequence[SearchChunk],
    ) -> None:
        for start in range(0, len(chunks), _UPSERT_BATCH_SIZE):
            await self._client.upsert(
                self._collection,
                points=[self._to_point(chunk) for chunk in chunks[start : start + _UPSERT_BATCH_SIZE]],
                wait=True,
            )

        stale = self._article_filter(article_id)
        stale.must_not = [
            models.FieldCondition(key="revision_id", match=models.MatchValue(value=str(revision_id)))
        ]
        await self._client.delete(
            self._collection, points_selector=models.FilterSelector(filter=stale), wait=True
        )

    async def delete_article_chunks(self, article_id: UUID) -> None:
        await self._client.delete(
            self._collection,
            points_selector=models.FilterSelector(filter=self._article_filter(article_id)),
            wait=True,
        )

    async def find_article_vectors(self, article_id: UUID) -> dict[str, tuple[float, ...]]:
        vectors: dict[str, tuple[float, ...]] = {}
        offset = None

        while True:
            points, offset = await self._client.scroll(
                self._collection,
                scroll_filter=self._article_filter(article_id),
                with_payload=["content_hash"],
                with_vectors=[DENSE_VECTOR],
                limit=256,
                offset=offset,
            )
            for point in points:
                vector = (point.vector or {}).get(DENSE_VECTOR) if isinstance(point.vector, dict) else None
                if point.payload and vector:
                    vectors[point.payload["content_hash"]] = tuple(vector)

            if offset is None:
                return vectors

    @staticmethod
    def _scope_filter(organization_id: UUID, scope: SearchScope) -> models.Filter:
        """``organization AND (space IN scope OR article IN scope) [AND space IN restrict]``."""

        must: list[models.Condition] = [
            models.FieldCondition(key="organization_id", match=models.MatchValue(value=str(organization_id))),
        ]
        if scope.restrict_space_ids is not None:
            must.append(
                models.FieldCondition(
                    key="space_id",
                    match=models.MatchAny(any=[str(item) for item in scope.restrict_space_ids]),
                )
            )

        should: list[models.Condition] = [
            models.FieldCondition(key=key, match=models.MatchAny(any=[str(item) for item in ids]))
            for key, ids in (("space_id", scope.space_ids), ("article_id", scope.article_ids))
            if ids
        ]
        return models.Filter(must=must, should=should)

    async def search(
        self,
        *,
        query: str,
        query_vector: Sequence[float],
        organization_id: UUID,
        scope: SearchScope,
        limit: int,
        hits_per_article: int,
    ) -> list[ArticleHits]:
        if scope.is_empty:
            return []

        scope_filter = self._scope_filter(organization_id, scope)
        prefetch_limit = limit * hits_per_article * _PREFETCH_FACTOR

        response = await self._client.query_points_groups(
            self._collection,
            group_by="article_id",
            prefetch=[
                models.Prefetch(
                    query=list(query_vector),
                    using=DENSE_VECTOR,
                    filter=scope_filter,
                    limit=prefetch_limit,
                ),
                models.Prefetch(
                    query=self._bm25_document(query),
                    using=BM25_VECTOR,
                    filter=scope_filter,
                    limit=prefetch_limit,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            query_filter=scope_filter,
            limit=limit,
            group_size=hits_per_article,
            with_payload=_HIT_PAYLOAD,
        )

        results: list[ArticleHits] = []
        for group in response.groups:
            hits = tuple(
                ChunkHit(
                    chunk_id=UUID(str(point.id)),
                    article_id=UUID(point.payload["article_id"]),
                    revision_id=UUID(point.payload["revision_id"]),
                    score=point.score,
                    text=point.payload["text"],
                    heading_path=tuple(point.payload.get("heading_path") or ()),
                    anchor=point.payload.get("anchor"),
                )
                for point in group.hits
                if point.payload
            )
            if hits:
                results.append(ArticleHits(article_id=hits[0].article_id, score=hits[0].score, hits=hits))

        return results
