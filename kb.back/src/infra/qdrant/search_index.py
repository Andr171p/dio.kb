from collections.abc import Sequence
from http import HTTPStatus
from uuid import UUID

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from src.application.indexing.models import IndexedChunk
from src.application.search.access import SearchScope
from src.application.search.indexes import SearchOptions
from src.application.search.models import ArticleMatch, ChunkHit

from .config import QdrantConfig

DENSE_VECTOR = "dense"
BM25_VECTOR = "bm25"
BM25_MODEL = "qdrant/bm25"

_PREFETCH_FACTOR = 5
_HIT_PAYLOAD = ["article_id", "revision_id", "text", "heading_path", "anchor"]


def _scope_filter(scope: SearchScope, space_ids: Sequence[UUID] | None) -> models.Filter:
    must: list[models.Condition] = [
        models.FieldCondition(
            key="organization_id",
            match=models.MatchValue(value=str(scope.organization_id)),
        )
    ]

    if space_ids is not None:
        must.append(
            models.FieldCondition(
                key="space_id",
                match=models.MatchAny(any=[str(space_id) for space_id in space_ids]),
            )
        )

    should: list[models.Condition] = [
        models.FieldCondition(
            key=kind + "_id",
            match=models.MatchAny(any=[str(r.id) for r in scope.resources if r.type == kind]),
        )
        for kind in ("space", "article")
        if any(r.type == kind for r in scope.resources)
    ]

    must.append(models.Filter(should=should))
    return models.Filter(must=must)


def _article_filter(organization_id: UUID, article_id: UUID) -> models.Filter:
    return models.Filter(
        must=[
            models.FieldCondition(key="organization_id", match=models.MatchValue(value=str(organization_id))),
            models.FieldCondition(key="article_id", match=models.MatchValue(value=str(article_id))),
        ]
    )


class QdrantSearchIndex:
    """
    Фрагменты в Qdrant: dense-вектор (embedding) + sparse BM25, вычисляемый на сервере Qdrant.
    Поиск — гибридный (RRF двух prefetch), всегда с фильтром области доступа.
    """

    def __init__(self, config: QdrantConfig, *, write_batch_size: int = 100) -> None:
        if write_batch_size < 1:
            raise ValueError("write_batch_size must be positive")
        self._write_batch_size = write_batch_size
        self._client = AsyncQdrantClient(
            url=str(config.url),
            api_key=config.api_key.get_secret_value() if config.api_key else None,
            timeout=config.timeout,
            cloud_inference=True,
        )
        self._config = config
        self._collection = config.collection_name

    @property
    def generation(self) -> str:
        return self._collection

    def _bm25_document(self, text: str) -> models.Document:
        """tokenizer по умолчанию ("word"): с "multilingual" русский стемминг не применяется"""
        return models.Document(text=text, model=BM25_MODEL, options={"language": self._config.bm25_language})

    async def ensure_collection(self, dense_size: int) -> None:
        """Создаёт коллекцию текущего поколения и payload-индексы, если их ещё нет."""

        if not await self._client.collection_exists(self._collection):
            try:
                await self._client.create_collection(
                    self._collection,
                    vectors_config={
                        DENSE_VECTOR: models.VectorParams(size=dense_size, distance=models.Distance.COSINE)
                    },
                    sparse_vectors_config={BM25_VECTOR: models.SparseVectorParams(modifier=models.Modifier.IDF)},
                )
            except UnexpectedResponse as exc:
                if exc.status_code != HTTPStatus.CONFLICT:
                    raise

        await self._client.create_payload_index(
            self._collection,
            "organization_id",
            models.KeywordIndexParams(type=models.KeywordIndexType.KEYWORD, is_tenant=True),
        )

        for field in ("space_id", "article_id", "revision_id"):
            await self._client.create_payload_index(self._collection, field, models.PayloadSchemaType.KEYWORD)

    def _to_point(self, chunk: IndexedChunk) -> models.PointStruct:
        return models.PointStruct(
            id=str(chunk.id),
            vector={
                DENSE_VECTOR: list(chunk.embedding or ()),
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
                "text": chunk.markdown,
                "content_hash": chunk.content_hash,
                "media_ids": [str(media_id) for media_id in chunk.media_ids],
            },
        )

    async def sync_revision(
        self,
        *,
        organization_id: UUID,
        article_id: UUID,
        revision_id: UUID,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        if any(
            c.organization_id != organization_id
            or c.article_id != article_id
            or c.revision_id != revision_id
            or not c.embedding
            for c in chunks
        ):
            raise ValueError("Invalid chunks for article revision")

        for start in range(0, len(chunks), self._write_batch_size):
            await self._client.upsert(
                self._collection,
                points=[self._to_point(c) for c in chunks[start : start + self._write_batch_size]],
                wait=True,
            )

        stale = _article_filter(organization_id, article_id)
        ids: list[models.ExtendedPointId] = [str(c.id) for c in chunks]

        if ids:
            stale.must_not = [models.HasIdCondition(has_id=ids)]

        await self._client.delete(self._collection, points_selector=models.FilterSelector(filter=stale), wait=True)

    async def delete_article(self, *, organization_id: UUID, article_id: UUID) -> None:
        await self._client.delete(
            self._collection,
            points_selector=models.FilterSelector(filter=_article_filter(organization_id, article_id)),
            wait=True,
        )

    async def search(
        self,
        *,
        query: str,
        query_embedding: Sequence[float],
        scope: SearchScope,
        space_ids: Sequence[UUID] | None,
        options: SearchOptions,
    ) -> list[ArticleMatch]:
        if not any(resource.type in {"space", "article"} for resource in scope.resources):
            return []

        if space_ids is not None and not space_ids:
            return []

        scope_filter = _scope_filter(scope, space_ids)
        prefetch_limit = options.candidates_limit * options.max_hits_per_article * _PREFETCH_FACTOR

        response = await self._client.query_points_groups(
            self._collection,
            group_by="article_id",
            prefetch=[
                models.Prefetch(
                    query=list(query_embedding),
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
            limit=options.candidates_limit,
            group_size=options.max_hits_per_article,
            with_payload=_HIT_PAYLOAD,
        )

        results: list[ArticleMatch] = []
        for group in response.groups:
            hits = tuple(
                ChunkHit(
                    chunk_id=UUID(str(point.id)),
                    article_id=UUID(point.payload["article_id"]),
                    revision_id=UUID(point.payload["revision_id"]),
                    score=point.score,
                    markdown=point.payload["text"],
                    heading_path=tuple(point.payload.get("heading_path") or ()),
                    anchor=point.payload.get("anchor"),
                )
                for point in group.hits
                if point.payload
            )
            if hits:
                results.append(ArticleMatch(article_id=hits[0].article_id, score=hits[0].score, hits=hits))

        return results

    async def close(self) -> None:
        await self._client.close()
