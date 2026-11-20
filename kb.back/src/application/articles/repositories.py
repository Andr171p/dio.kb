from typing import override

from collections.abc import Collection, Sequence
from uuid import UUID

from ddf.application.repositories import Repository

from src.domain.access.vo import Subject
from src.domain.articles.models import Article, ArticleRevision

from .dtos import ArticleSummaryResponse
from .projections import PublishedArticle


class ArticleRepository(Repository[Article]):
    @override
    async def read(self, uid: UUID, with_lock: bool = False) -> Article | None: ...

    async def find_by_slug(self, space_id: UUID, slug: str) -> Article | None: ...


class ArticleRevisionRepository(Repository[ArticleRevision]):
    async def find_by_article(self, article_id: UUID) -> tuple[ArticleRevision, ...]:
        """Редакции статьи, новые первыми."""


class ArticleQueryRepository:
    """Read-модели статей (JOIN с редакциями), не нагружающие репозиторий агрегата."""

    async def find_space_articles(self, space_id: UUID, *, include_drafts: bool) -> tuple[ArticleSummaryResponse, ...]:
        """Не архивные статьи Space; заголовок из текущей (``include_drafts``) или опубликованной редакции."""

    async def find_published(
        self,
        organization_id: UUID,
        article_ids: Collection[UUID],
    ) -> tuple[PublishedArticle, ...]:
        """Опубликованные неархивный статьи в активных Space организации."""

    async def find_readable_published(
        self,
        organization_id: UUID,
        article_ids: Collection[UUID],
        *,
        subjects: Collection[Subject],
        space_ids: Collection[UUID] | None = None,
    ) -> Sequence[PublishedArticle]:
        """
        Вернуть опубликованные статьи, доступные на чтение.

        Проверяет актуальные:
        - организацию и публикацию;
        - состояние пространства и статьи;
        - READ grants, включая PUBLIC;
        - membership и роли пользователя.

        Не использует ранее вычисленный SearchScope.
        """


__all__ = ["ArticleQueryRepository", "ArticleRepository", "ArticleRevisionRepository"]
