from uuid import UUID

from ddf.infra.database.sqlalchemy import SqlAlchemyRepository
from sqlalchemy import select

from src.application.articles.repositories import (
    ArticleRevisionRepository,
)
from src.domain.articles.models import ArticleRevision

from ..models import ArticleRevisionOrm


class ArticleRevisionMapper:
    @staticmethod
    def to_model(entity: ArticleRevision) -> ArticleRevisionOrm:
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

    @staticmethod
    def from_model(model: ArticleRevisionOrm) -> ArticleRevision:
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


class SqlAlchemyArticleRevisionRepository(SqlAlchemyRepository[ArticleRevision, ArticleRevisionOrm]):
    model = ArticleRevisionOrm
    data_mapper = ArticleRevisionMapper()

    async def find_by_article(self, article_id: UUID) -> tuple[ArticleRevision, ...]:
        stmt = (
            select(ArticleRevisionOrm)
            .where(ArticleRevisionOrm.article_id == article_id)
            .order_by(ArticleRevisionOrm.number.desc())
        )
        return tuple(self.data_mapper.from_model(model) for model in await self._session.scalars(stmt))
