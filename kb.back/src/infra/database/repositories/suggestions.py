from collections.abc import Collection, Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.search.access import SearchScope
from src.infra.database.models import ArticleOrm, ArticleRevisionOrm, SpaceOrm


class SqlAlchemySuggestionIndex:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def suggest(
        self,
        query: str,
        *,
        scope: SearchScope,
        space_ids: Collection[UUID] | None,
        limit: int,
    ) -> Sequence[UUID]:
        spaces = [r.id for r in scope.resources if r.type == "space"]
        articles = [r.id for r in scope.resources if r.type == "article"]

        if not (spaces or articles) or (space_ids is not None and not space_ids):
            return ()

        # Escape SQL LIKE wildcards so user input remains literal.
        term = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        stmt = (
            select(ArticleOrm.id)
            .join(ArticleRevisionOrm, ArticleRevisionOrm.id == ArticleOrm.published_revision_id)
            .join(SpaceOrm, SpaceOrm.id == ArticleOrm.space_id)
            .where(
                ArticleOrm.organization_id == scope.organization_id,
                ArticleOrm.deleted_at.is_(None),
                SpaceOrm.deleted_at.is_(None),
                or_(ArticleOrm.space_id.in_(spaces), ArticleOrm.id.in_(articles)),
                ArticleRevisionOrm.title.ilike(f"%{term}%", escape="\\"),
            )
        )

        if space_ids is not None:
            stmt = stmt.where(ArticleOrm.space_id.in_(space_ids))

        return tuple(await self._session.scalars(stmt.order_by(ArticleRevisionOrm.title, ArticleOrm.id).limit(limit)))
