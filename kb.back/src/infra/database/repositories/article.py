from typing import override

from uuid import UUID

from ddf.infra.database.sqlalchemy import SqlAlchemyRepository
from sqlalchemy import select

from src.application.articles.repositories import (
    ArticleRepository,
)
from src.domain.articles.models import Article

from ..models import ArticleOrm


class ArticleMapper:
    @staticmethod
    def to_model(entity: Article) -> ArticleOrm:
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

    @staticmethod
    def from_model(model: ArticleOrm) -> Article:
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
