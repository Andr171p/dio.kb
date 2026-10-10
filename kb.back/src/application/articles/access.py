from uuid import UUID

from ddf.application.exceptions import NotFoundError

from src.application.access import (
    AccessGrantRepository,
    Permission,
    Resource,
    ensure_access,
    resolve_permissions,
)
from src.application.auth.dtos import AuthUser
from src.domain.articles.models import Article

from .repositories import ArticleRepository


async def get_accessible_article(
    article_id: UUID,
    auth: AuthUser,
    required: Permission,
    *,
    article_repository: ArticleRepository,
    grant_repository: AccessGrantRepository,
    with_lock: bool = False,
) -> Article:
    """Загружает статью организации пользователя и проверяет права с учётом её Space."""

    article = await article_repository.read(article_id, with_lock=with_lock)

    if article is None or article.organization_id != auth.user.organization_id:
        raise NotFoundError(f"Article with ID {article_id} not found.")

    await ensure_access(auth, article_resources(article), required, grant_repository=grant_repository)
    return article


def article_resources(article: Article) -> tuple[Resource, ...]:
    """Цепочка ресурсов, права на которые действуют на статью."""

    return Resource(type="space", id=article.space_id), Resource(type="article", id=article.id)


async def resolve_article_permissions(
    article: Article, auth: AuthUser, *, grant_repository: AccessGrantRepository
) -> Permission:
    return await resolve_permissions(auth, article_resources(article), grant_repository=grant_repository)


__all__ = ["article_resources", "get_accessible_article", "resolve_article_permissions"]
