from collections.abc import AsyncIterator, Collection, Mapping
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.indexing.checkpoint import IndexCheckpoint
from src.application.indexing.image_analysis import ImageAnalysis
from src.application.indexing.reconciliation import ReconciliationQuery
from src.domain.articles.models import PublishedArticle
from src.infra.database.models import (
    ArticleOrm,
    ArticleRevisionOrm,
    EmbeddingOrm,
    ImageAnalysisOrm,
    IndexCheckpointOrm,
    SpaceOrm,
)
from src.infra.database.repositories.article import ArticleMapper
from src.infra.database.repositories.revision import ArticleRevisionMapper


class SqlAlchemyIndexingRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def load_publication(self, organization_id: UUID, article_id: UUID) -> PublishedArticle | None:
        async with self._sessionmaker() as session:
            row = (
                await session.execute(
                    select(ArticleOrm, ArticleRevisionOrm)
                    .join(ArticleRevisionOrm, ArticleRevisionOrm.id == ArticleOrm.published_revision_id)
                    .join(SpaceOrm, SpaceOrm.id == ArticleOrm.space_id)
                    .where(
                        ArticleOrm.id == article_id,
                        ArticleOrm.organization_id == organization_id,
                        ArticleOrm.deleted_at.is_(None),
                        SpaceOrm.deleted_at.is_(None),
                    )
                )
            ).one_or_none()
            return (ArticleMapper.from_model(row[0]), ArticleRevisionMapper.from_model(row[1])) if row else None

    @asynccontextmanager
    async def lock_article(self, organization_id: UUID, article_id: UUID) -> AsyncIterator[None]:
        async with self._sessionmaker() as session, session.begin():
            await session.execute(
                select(
                    func.pg_advisory_xact_lock(
                        func.hashtextextended(f"article-index:{organization_id}:{article_id}", 0)
                    )
                )
            )
            yield

    async def get(self, article_id: UUID, generation: str) -> IndexCheckpoint | None:
        async with self._sessionmaker() as session:
            row = await session.get(IndexCheckpointOrm, (article_id, generation))
            return (
                IndexCheckpoint(row.article_id, row.revision_id, row.space_id, row.generation, row.indexed_at)
                if row
                else None
            )

    async def save_if_current(self, organization_id: UUID, checkpoint: IndexCheckpoint) -> bool:
        async with self._sessionmaker() as session, session.begin():
            article = await session.scalar(
                select(ArticleOrm)
                .join(SpaceOrm, SpaceOrm.id == ArticleOrm.space_id)
                .where(
                    SpaceOrm.deleted_at.is_(None),
                    ArticleOrm.id == checkpoint.article_id,
                    ArticleOrm.organization_id == organization_id,
                    ArticleOrm.deleted_at.is_(None),
                    ArticleOrm.published_revision_id == checkpoint.revision_id,
                    ArticleOrm.space_id == checkpoint.space_id,
                )
                .with_for_update(of=ArticleOrm)
            )
            if article is None:
                return False
            stmt = insert(IndexCheckpointOrm).values(
                article_id=checkpoint.article_id,
                generation=checkpoint.generation,
                revision_id=checkpoint.revision_id,
                space_id=checkpoint.space_id,
                indexed_at=checkpoint.indexed_at,
            )
            await session.execute(
                stmt.on_conflict_do_update(
                    index_elements=[IndexCheckpointOrm.article_id, IndexCheckpointOrm.generation],
                    set_={
                        "revision_id": checkpoint.revision_id,
                        "space_id": checkpoint.space_id,
                        "indexed_at": checkpoint.indexed_at,
                    },
                )
            )
            return True

    async def clear_if_unpublished(self, organization_id: UUID, article_id: UUID, generation: str) -> bool:
        async with self._sessionmaker() as session, session.begin():
            article = await session.scalar(select(ArticleOrm).where(ArticleOrm.id == article_id).with_for_update())
            if article is not None:
                if article.organization_id != organization_id:
                    return False
                space = await session.get(SpaceOrm, article.space_id)
                if (
                    article.deleted_at is None
                    and article.published_revision_id is not None
                    and space is not None
                    and space.deleted_at is None
                ):
                    return False
            await session.execute(
                delete(IndexCheckpointOrm).where(
                    IndexCheckpointOrm.article_id == article_id, IndexCheckpointOrm.generation == generation
                )
            )
            return True

    async def find_candidates(self, query: ReconciliationQuery) -> tuple[UUID, ...]:
        published = and_(
            ArticleOrm.deleted_at.is_(None),
            ArticleOrm.published_revision_id.is_not(None),
            SpaceOrm.deleted_at.is_(None),
        )
        async with self._sessionmaker() as session:
            stmt = (
                select(ArticleOrm.id)
                .join(SpaceOrm, SpaceOrm.id == ArticleOrm.space_id)
                .outerjoin(
                    IndexCheckpointOrm,
                    and_(
                        IndexCheckpointOrm.article_id == ArticleOrm.id,
                        IndexCheckpointOrm.generation == query.generation,
                    ),
                )
                .where(ArticleOrm.organization_id == query.organization_id)
            )
            if query.mode == "rebuild":
                stmt = stmt.where(or_(published, IndexCheckpointOrm.article_id.is_not(None)))
            else:
                stmt = stmt.where(
                    or_(
                        and_(
                            published,
                            or_(
                                IndexCheckpointOrm.article_id.is_(None),
                                IndexCheckpointOrm.revision_id.is_distinct_from(ArticleOrm.published_revision_id),
                                IndexCheckpointOrm.space_id.is_distinct_from(ArticleOrm.space_id),
                            ),
                        ),
                        and_(~published, IndexCheckpointOrm.article_id.is_not(None)),
                    )
                )
            if query.after_id is not None:
                stmt = stmt.where(ArticleOrm.id > query.after_id)
            return tuple(await session.scalars(stmt.order_by(ArticleOrm.id).limit(query.limit)))


class SqlAlchemyImageAnalysisCache:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def get_many(self, media_ids: Collection[UUID], version: str) -> dict[UUID, ImageAnalysis]:
        async with self._sessionmaker() as session:
            rows = await session.scalars(
                select(ImageAnalysisOrm).where(
                    ImageAnalysisOrm.media_id.in_(media_ids), ImageAnalysisOrm.version == version
                )
            )
            return {row.media_id: ImageAnalysis(text=row.text, description=row.description) for row in rows}

    async def put(self, media_id: UUID, version: str, analysis: ImageAnalysis) -> None:
        async with self._sessionmaker() as session, session.begin():
            await session.execute(
                insert(ImageAnalysisOrm)
                .values(media_id=media_id, version=version, text=analysis.text, description=analysis.description)
                .on_conflict_do_nothing()
            )


class SqlAlchemyEmbeddingCache:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def get_many(self, content_hashes: Collection[str], version: str) -> dict[str, tuple[float, ...]]:
        async with self._sessionmaker() as session:
            rows = await session.scalars(
                select(EmbeddingOrm).where(
                    EmbeddingOrm.content_hash.in_(content_hashes), EmbeddingOrm.version == version
                )
            )
            return {row.content_hash: tuple(row.vector) for row in rows}

    async def put_many(self, embeddings: Mapping[str, tuple[float, ...]], version: str) -> None:
        if embeddings:
            async with self._sessionmaker() as session, session.begin():
                await session.execute(
                    insert(EmbeddingOrm)
                    .values(
                        [
                            {"content_hash": key, "version": version, "vector": list(vector)}
                            for key, vector in embeddings.items()
                        ]
                    )
                    .on_conflict_do_nothing()
                )
