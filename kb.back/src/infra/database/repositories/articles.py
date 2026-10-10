from typing import override

from collections.abc import Collection
from uuid import UUID

from ddf.infra.database.sqlalchemy import SqlAlchemyRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.articles.dtos import ArticleSummaryResponse
from src.application.articles.models import PublishedArticle
from src.application.articles.repositories import (
    ArticleQueryRepository,
    ArticleRepository,
    ArticleRevisionRepository,
)
from src.domain.articles.models import Article, ArticleRevision
from src.domain.articles.types import ArticleStatus

from ..models import ArticleOrm, ArticleRevisionOrm, SpaceOrm


class ArticleMapper:
    def to_model(self, entity: Article) -> ArticleOrm:
        return ArticleOrm(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
            organization_id=entity.organization_id,
            space_id=entity.space_id,
            slug=entity.slug,
            current_revision_id=entity.current_revision_id,
            published_revision_id=entity.published_revision_id,
            revision_number=entity.revision_number,
            author_id=entity.author_id,
            published_at=entity.published_at,
        )

    def from_model(self, model: ArticleOrm) -> Article:
        return Article(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            organization_id=model.organization_id,
            space_id=model.space_id,
            slug=model.slug,
            current_revision_id=model.current_revision_id,
            published_revision_id=model.published_revision_id,
            revision_number=model.revision_number,
            author_id=model.author_id,
            published_at=model.published_at,
        )


class ArticleRevisionMapper:
    def to_model(self, entity: ArticleRevision) -> ArticleRevisionOrm:
        return ArticleRevisionOrm(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
            article_id=entity.article_id,
            number=entity.number,
            previous_revision_id=entity.previous_revision_id,
            restored_from_revision_id=entity.restored_from_revision_id,
            title=entity.title,
            summary=entity.summary,
            content=entity.content,
            author_id=entity.author_id,
            change_note=entity.change_note,
        )

    def from_model(self, model: ArticleRevisionOrm) -> ArticleRevision:
        return ArticleRevision(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            article_id=model.article_id,
            number=model.number,
            previous_revision_id=model.previous_revision_id,
            restored_from_revision_id=model.restored_from_revision_id,
            title=model.title,
            summary=model.summary,
            content=model.content,
            author_id=model.author_id,
            change_note=model.change_note,
        )


class SqlAlchemyArticleRepository(SqlAlchemyRepository[Article, ArticleOrm], ArticleRepository):
    model = ArticleOrm
    data_mapper = ArticleMapper()

    @override
    async def read(self, uid: UUID, with_lock: bool = False) -> Article | None:
        stmt = select(ArticleOrm).where(ArticleOrm.id == uid)
        if with_lock:
            stmt = stmt.with_for_update()

        model = await self._session.scalar(stmt)
        return None if model is None else self.data_mapper.from_model(model)

    async def find_by_slug(self, space_id: UUID, slug: str) -> Article | None:
        stmt = select(ArticleOrm).where(ArticleOrm.space_id == space_id, ArticleOrm.slug == slug)
        model = await self._session.scalar(stmt)
        return None if model is None else self.data_mapper.from_model(model)


class SqlAlchemyArticleRevisionRepository(
    SqlAlchemyRepository[ArticleRevision, ArticleRevisionOrm],
    ArticleRevisionRepository,
):
    model = ArticleRevisionOrm
    data_mapper = ArticleRevisionMapper()

    async def find_by_article(self, article_id: UUID) -> tuple[ArticleRevision, ...]:
        stmt = (
            select(ArticleRevisionOrm)
            .where(ArticleRevisionOrm.article_id == article_id)
            .order_by(ArticleRevisionOrm.number.desc())
        )
        return tuple(self.data_mapper.from_model(model) for model in await self._session.scalars(stmt))


class SqlAlchemyArticleQueryRepository(ArticleQueryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_space_articles(
        self, space_id: UUID, *, include_drafts: bool
    ) -> tuple[ArticleSummaryResponse, ...]:
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
