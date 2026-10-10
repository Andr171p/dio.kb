from typing import override

from collections.abc import Collection
from uuid import UUID

from ddf.application.repositories import Repository

from src.domain.articles.models import Article, ArticleRevision

from .dtos import ArticleSummaryResponse
from .models import PublishedArticle


class ArticleRepository(Repository[Article]):
    @override
    async def read(self, uid: UUID, with_lock: bool = False) -> Article | None: ...

    async def find_by_slug(self, space_id: UUID, slug: str) -> Article | None: ...


class ArticleRevisionRepository(Repository[ArticleRevision]):
    async def find_by_article(self, article_id: UUID) -> tuple[ArticleRevision, ...]:
        """Редакции статьи, новые первыми."""


class ArticleQueryRepository:
    """Read-модели статей (JOIN с редакциями), не нагружающие репозиторий агрегата."""

    async def find_space_articles(
        self, space_id: UUID, *, include_drafts: bool
    ) -> tuple[ArticleSummaryResponse, ...]:
        """Неархивные статьи Space; заголовок из текущей (``include_drafts``) или опубликованной редакции."""

    async def find_published(
        self,
        organization_id: UUID,
        article_ids: Collection[UUID],
    ) -> tuple[PublishedArticle, ...]:
        """Опубликованные неархивные статьи в активных Space организации."""


__all__ = ["ArticleQueryRepository", "ArticleRepository", "ArticleRevisionRepository"]
