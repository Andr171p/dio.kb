from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.search.models import ArticleIndexState, ImageText

from ..models import ArticleIndexStateOrm, ArticleOrm, ImageTextOrm


class SqlAlchemyImageTextRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find(self, media_ids: Sequence[UUID], version: str) -> dict[UUID, ImageText]:
        if not media_ids:
            return {}

        stmt = select(ImageTextOrm).where(
            ImageTextOrm.media_id.in_(media_ids), ImageTextOrm.version == version
        )
        return {
            model.media_id: ImageText(text=model.text, description=model.description)
            for model in await self._session.scalars(stmt)
        }

    async def save(self, media_id: UUID, version: str, image_text: ImageText) -> None:
        stmt = insert(ImageTextOrm).values(
            media_id=media_id,
            version=version,
            text=image_text.text,
            description=image_text.description,
        )
        await self._session.execute(stmt.on_conflict_do_nothing())


class SqlAlchemyArticleIndexStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lock(self, article_id: UUID) -> None:
        key = f"article-index:{article_id}"
        await self._session.execute(select(func.pg_advisory_xact_lock(func.hashtextextended(key, 0))))

    async def save(self, state: ArticleIndexState) -> None:
        values = {
            "revision_id": state.revision_id,
            "index_name": state.index_name,
            "chunk_count": state.chunk_count,
            "failed_media_ids": list(state.failed_media_ids),
            "indexed_at": state.indexed_at,
        }
        stmt = insert(ArticleIndexStateOrm).values(article_id=state.article_id, **values)
        await self._session.execute(
            stmt.on_conflict_do_update(index_elements=[ArticleIndexStateOrm.article_id], set_=values),
        )

    async def find_out_of_sync_article_ids(self, index_name: str, *, full: bool = False) -> tuple[UUID, ...]:
        is_published = and_(ArticleOrm.deleted_at.is_(None), ArticleOrm.published_revision_id.is_not(None))

        if full:
            stmt = (
                select(ArticleOrm.id)
                .outerjoin(ArticleIndexStateOrm, ArticleIndexStateOrm.article_id == ArticleOrm.id)
                .where(or_(is_published, ArticleIndexStateOrm.revision_id.is_not(None)))
            )
            return tuple(await self._session.scalars(stmt))

        stmt = (
            select(ArticleOrm.id)
            .outerjoin(ArticleIndexStateOrm, ArticleIndexStateOrm.article_id == ArticleOrm.id)
            .where(
                or_(
                    and_(
                        is_published,
                        or_(
                            ArticleIndexStateOrm.article_id.is_(None),
                            ArticleIndexStateOrm.index_name != index_name,
                            ArticleIndexStateOrm.revision_id.is_distinct_from(
                                ArticleOrm.published_revision_id
                            ),
                        ),
                    ),
                    and_(~is_published, ArticleIndexStateOrm.revision_id.is_not(None)),
                )
            )
        )
        return tuple(await self._session.scalars(stmt))
