from uuid import UUID

from ddf.application.exceptions import NotFoundError

from src.application.access import AccessGrantRepository, Permission, Resource, ensure_access
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

    resources = (Resource(type="space", id=article.space_id), Resource(type="article", id=article.id))
    await ensure_access(auth, resources, required, grant_repository=grant_repository)
    return article


__all__ = ["get_accessible_article"]
