# RULE: Избегай использования безсполезных функий

 - Не нужно называть функцию существительным, если её по другому адеватно не назвать, то нужно задуматься нужна ли здесь функция

**Например**

`src/application/articles/access.py`
```python
from ddf.application.exceptions import NotFoundError

from src.application.access.repositories import AccessGrantRepository
from src.application.access.services import ensure_access
from src.application.auth.dtos import AuthUser
from src.domain.access.types import Permission
from src.domain.access.vo import Resource
from src.domain.articles.models import Article


def _article_resources(article: Article) -> tuple[Resource, ...]:
    return (Resource(type="space", id=article.space_id), Resource(type="article", id=article.id))


async def ensure_article_access(
    article: Article,
    auth: AuthUser,
    required: Permission,
    *,
    grant_repository: AccessGrantRepository,
) -> None:
    """Проверяет доступ к статье с учётом рабочего пространства."""

    if article.organization_id != auth.user.organization_id:
        raise NotFoundError(f"Article with ID {article.id!r} not found.")

    resources = _article_resources(article)
    await ensure_access(auth, resources, required, grant_repository=grant_repository)


__all__ = ["ensure_article_access"]

```

В этом примере можно было обойтись без `_article_resources`, а просто реализовать внутри `ensure_article_access`.
