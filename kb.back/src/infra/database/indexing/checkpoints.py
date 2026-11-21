from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.indexing.checkpoint import IndexCheckpoint
from src.infra.database.models import ArticleOrm, IndexCheckpointOrm, SpaceOrm


class SqlAlchemyIndexCheckpointStore:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def get(self, article_id: UUID, generation: str) -> IndexCheckpoint | None:
        async with self._sessionmaker() as session:
            if (row := await session.get(IndexCheckpointOrm, (article_id, generation))) is None:
                return None

            return IndexCheckpoint(
                article_id=row.article_id,
                revision_id=row.revision_id,
                space_id=row.space_id,
                generation=row.generation,
                indexed_at=row.indexed_at,
            )

    async def save_if_current(self, organization_id: UUID, checkpoint: IndexCheckpoint) -> bool:
        """Подтверждает индекс только для актуальной публикации."""

        stmt = (
            select(ArticleOrm.id)
            .join(
                SpaceOrm,
                and_(
                    SpaceOrm.id == ArticleOrm.space_id,
                    SpaceOrm.organization_id == ArticleOrm.organization_id,
                ),
            )
            .where(
                ArticleOrm.id == checkpoint.article_id,
                ArticleOrm.organization_id == organization_id,
                ArticleOrm.deleted_at.is_(None),
                ArticleOrm.published_revision_id == checkpoint.revision_id,
                ArticleOrm.space_id == checkpoint.space_id,
                SpaceOrm.deleted_at.is_(None),
            )
            .with_for_update(of=(ArticleOrm, SpaceOrm))
        )

        async with self._sessionmaker.begin() as session:
            if await session.scalar(stmt) is None:
                return False

            upsert = (
                insert(IndexCheckpointOrm)
                .values(
                    article_id=checkpoint.article_id,
                    revision_id=checkpoint.revision_id,
                    space_id=checkpoint.space_id,
                    generation=checkpoint.generation,
                    indexed_at=checkpoint.indexed_at,
                )
                .on_conflict_do_update(
                    index_elements=["article_id", "generation"],
                    set_={
                        "revision_id": checkpoint.revision_id,
                        "space_id": checkpoint.space_id,
                        "indexed_at": checkpoint.indexed_at,
                    },
                )
            )
            await session.execute(upsert)

        return True

    async def clear_if_unpublished(self, organization_id: UUID, article_id: UUID, generation: str) -> bool:
        async with self._sessionmaker() as session, session.begin():
            stmt = select(ArticleOrm).where(ArticleOrm.id == article_id).with_for_update()

            if (article := await session.scalar(stmt)) is not None:
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

            stmt = (
                delete(IndexCheckpointOrm)
                .where(IndexCheckpointOrm.article_id == article_id, IndexCheckpointOrm.generation == generation)
            )
            await session.execute(stmt)
            return True


__all__ = ["SqlAlchemyIndexCheckpointStore"]
