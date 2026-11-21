from typing import Annotated

from urllib.parse import urljoin
from uuid import UUID

from ddf.application.exceptions import NotFoundError
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field, PositiveInt

from src.application.access.exceptions import AccessDeniedError
from src.application.articles import usecases as articles
from src.application.search import usecases as search
from src.application.search.dtos import SearchRequest, SearchText
from src.application.spaces import usecases as spaces

from .auth import CurrentMcpUser
from .config import mcp_config
from .dependencies import (
    ArticleQueryRepositoryDep,
    ArticleRepositoryDep,
    GrantRepositoryDep,
    RevisionRepositoryDep,
    SearchIndexDep,
    SpaceRepositoryDep,
    TextEmbedderDep,
)
from .dtos import KnowledgeArticle, KnowledgeMatch, KnowledgeSearchResult, KnowledgeSpace, KnowledgeSpacesResult


def _build_article_url(article_id: UUID) -> str:
    return urljoin(str(mcp_config.resource_url), f"/articles/{article_id}")


async def search_knowledge(
    query: Annotated[SearchText, Field(description="Запрос или ключевые слова")],
    user: CurrentMcpUser,
    grant_repository: GrantRepositoryDep,
    article_query_repository: ArticleQueryRepositoryDep,
    search_index: SearchIndexDep,
    embedder: TextEmbedderDep,
    limit: Annotated[
        PositiveInt,
        Field(le=50, description="Максимальное число статей по убыванию релевантности"),
    ] = 10,
    space_ids: Annotated[
        list[UUID] | None,
        Field(
            max_length=100,
            description="UUID пространств из get_spaces. Пропустите для поиска по всем доступным статьям.",
        ),
    ] = None,
) -> KnowledgeSearchResult:
    """Ищет доступные опубликованные статьи. Возвращает фрагменты, ссылки и article_id для get_article."""

    result = await search.search_articles(
        user.user.organization_id,
        user,
        SearchRequest(query=query, limit=limit, space_ids=space_ids),
        grant_repository=grant_repository,
        article_query_repository=article_query_repository,
        search_index=search_index,
        embedder=embedder,
    )

    return KnowledgeSearchResult(
        items=[
            KnowledgeMatch(
                article_id=item.article.id,
                title=item.article.title,
                url=_build_article_url(item.article.id),
                fragments=[fragment.text for fragment in item.fragments],
            )
            for item in result.items
        ]
    )


async def get_article(
    article_id: Annotated[UUID, Field(description="UUID статьи из поля article_id результата search_knowledge.")],
    user: CurrentMcpUser,
    article_repository: ArticleRepositoryDep,
    revision_repository: RevisionRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> KnowledgeArticle:
    """Возвращает Markdown доступной опубликованной статьи по её UUID, когда поисковых фрагментов недостаточно."""

    try:
        result = await articles.get_published_article(
            article_id,
            user,
            article_repository=article_repository,
            revision_repository=revision_repository,
            grant_repository=grant_repository,
        )
    except (NotFoundError, AccessDeniedError):
        raise ToolError("Опубликованная статья недоступна.") from None

    return KnowledgeArticle(
        article_id=result.article.id,
        title=result.revision.title,
        url=_build_article_url(result.article.id),
        markdown=result.revision.content,
    )


async def get_spaces(
    user: CurrentMcpUser,
    space_repository: SpaceRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> KnowledgeSpacesResult:
    """Возвращает пространства для чтения. Передайте их UUID в space_ids инструмента search_knowledge."""

    result = await spaces.list_spaces(user, space_repository=space_repository, grant_repository=grant_repository)
    return KnowledgeSpacesResult(items=[KnowledgeSpace(id=space.id, name=space.name) for space in result])
