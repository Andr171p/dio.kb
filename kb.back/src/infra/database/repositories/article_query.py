from collections.abc import Collection
from uuid import UUID

from sqlalchemy import or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.articles.dtos import ArticleSummaryResponse
from src.application.articles.projections import PublishedArticle
from src.application.articles.repositories import (
    ArticleQueryRepository,
)
from src.domain.access.types import Permission
from src.domain.access.vo import Subject
from src.domain.articles.types import ArticleStatus

from ..models import AccessGrantOrm, ArticleOrm, ArticleRevisionOrm, SpaceOrm


class SqlAlchemyArticleQueryRepository(ArticleQueryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_space_articles(self, space_id: UUID, *, include_drafts: bool) -> tuple[ArticleSummaryResponse, ...]:
        revision_id = ArticleOrm.current_revision_id if include_drafts else ArticleOrm.published_revision_id
        stmt = (
            select(ArticleOrm, ArticleRevisionOrm.title)
            .join(ArticleRevisionOrm, ArticleRevisionOrm.id == revision_id)
            .where(ArticleOrm.space_id == space_id, ArticleOrm.deleted_at.is_(None))
            .order_by(ArticleRevisionOrm.title, ArticleOrm.id)
        )
        rows = await self._session.execute(stmt)

        return tuple(
            ArticleSummaryResponse(
                id=article.id,
                space_id=article.space_id,
                slug=article.slug,
                title=title,
                status=ArticleStatus.PUBLISHED if article.published_revision_id else ArticleStatus.DRAFT,
                updated_at=article.updated_at,
                published_at=article.published_at,
            )
            for article, title in rows.tuples()
        )

    async def find_published(
        self,
        organization_id: UUID,
        article_ids: Collection[UUID],
    ) -> tuple[PublishedArticle, ...]:
        if not article_ids:
            return ()

        stmt = (
            select(
                ArticleOrm.id,
                ArticleOrm.space_id,
                ArticleOrm.slug,
                ArticleRevisionOrm.title,
                ArticleOrm.published_revision_id,
                ArticleOrm.published_at,
            )
            .join(ArticleRevisionOrm, ArticleRevisionOrm.id == ArticleOrm.published_revision_id)
            .join(SpaceOrm, SpaceOrm.id == ArticleOrm.space_id)
            .where(
                ArticleOrm.id.in_(list(article_ids)),
                ArticleOrm.organization_id == organization_id,
                ArticleOrm.deleted_at.is_(None),
                SpaceOrm.deleted_at.is_(None),
            )
        )
        rows = await self._session.execute(stmt)
        return tuple(PublishedArticle(*row) for row in rows.tuples())

    async def find_readable_published(
        self,
        organization_id: UUID,
        article_ids: Collection[UUID],
        *,
        subjects: Collection[Subject],
        space_ids: Collection[UUID] | None = None,
    ) -> tuple[PublishedArticle, ...]:
        if not article_ids or not subjects or (space_ids is not None and not space_ids):
            return ()
        grants = select(AccessGrantOrm.resource_type, AccessGrantOrm.resource_id).where(
            AccessGrantOrm.organization_id == organization_id,
            AccessGrantOrm.deleted_at.is_(None),
            tuple_(AccessGrantOrm.subject_type, AccessGrantOrm.subject_id).in_(
                [(subject.type, subject.id) for subject in subjects]
            ),
            AccessGrantOrm.permissions.op("&")(int(Permission.READ)) == int(Permission.READ),
        )
        stmt = (
            select(
                ArticleOrm.id,
                ArticleOrm.space_id,
                ArticleOrm.slug,
                ArticleRevisionOrm.title,
                ArticleOrm.published_revision_id,
                ArticleOrm.published_at,
            )
            .join(ArticleRevisionOrm, ArticleRevisionOrm.id == ArticleOrm.published_revision_id)
            .join(SpaceOrm, SpaceOrm.id == ArticleOrm.space_id)
            .where(
                ArticleOrm.organization_id == organization_id,
                ArticleOrm.id.in_(article_ids),
                ArticleOrm.deleted_at.is_(None),
                SpaceOrm.deleted_at.is_(None),
                or_(tuple_("space", ArticleOrm.space_id).in_(grants), tuple_("article", ArticleOrm.id).in_(grants)),
            )
        )
        if space_ids is not None:
            stmt = stmt.where(ArticleOrm.space_id.in_(space_ids))
        return tuple(PublishedArticle(*row) for row in (await self._session.execute(stmt)).tuples())
