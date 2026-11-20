from uuid import UUID

from src.application.access import AccessGrantRepository, build_subjects_from_auth
from src.application.articles.repositories import ArticleQueryRepository
from src.application.auth import AuthUser

from .access import PUBLIC_SUBJECT, resolve_search_scope
from .dtos import (
    SearchArticle,
    SearchFragment,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SuggestionRequest,
    SuggestionResult,
    SuggestionsResponse,
)
from .indexes import SearchIndexReader, SearchOptions, SuggestionIndex
from .types import TextEmbedder

_SUGGESTION_OVERFETCH = 4


async def suggest_articles(
    organization_id: UUID,
    auth: AuthUser | None,
    dto: SuggestionRequest,
    *,
    grant_repository: AccessGrantRepository,
    article_query_repository: ArticleQueryRepository,
    suggestion_index: SuggestionIndex,
) -> SuggestionsResponse:
    """Подсказки по опубликованным статьям с актуальной проверкой ``READ``.

    Дешёвый и быстрый, не использует ембединги и не зависит от AI-провайдера.
    """

    if dto.space_ids is not None and not dto.space_ids:
        return SuggestionsResponse(items=[])

    scope = await resolve_search_scope(organization_id, auth, grant_repository=grant_repository)
    if scope.is_empty:
        return SuggestionsResponse(items=[])

    article_ids = list(
        dict.fromkeys(
            await suggestion_index.suggest(
                dto.query,
                scope=scope,
                space_ids=dto.space_ids,
                limit=dto.limit * _SUGGESTION_OVERFETCH,
            )
        )
    )

    readable = {
        article.id: article
        for article in await article_query_repository.find_readable_published(
            organization_id,
            article_ids,
            subjects=({PUBLIC_SUBJECT} | build_subjects_from_auth(auth)) if auth is not None else {PUBLIC_SUBJECT},
            space_ids=dto.space_ids,
        )
    }

    items: list[SuggestionResult] = []

    for article_id in article_ids:
        if (article := readable.get(article_id)) is None:
            continue

        items.append(
            SuggestionResult(
                article_id=article.id,
                space_id=article.space_id,
                slug=article.slug,
                title=article.title,
            )
        )

        if len(items) >= dto.limit:
            break

    return SuggestionsResponse(items=items)


async def search_articles(
    organization_id: UUID,
    auth: AuthUser | None,
    dto: SearchRequest,
    *,
    grant_repository: AccessGrantRepository,
    article_query_repository: ArticleQueryRepository,
    search_index: SearchIndexReader,
    embedder: TextEmbedder,
) -> SearchResponse:
    """
    Безопасный гибридный поиск по опубликованным статьям.

    Поисковый индекс может содержать устаревший ACL или даже временно вернуть слишком широкий набор кандидатов.
    Это не должно приводить к раскрытию данных.
    """

    if dto.space_ids is not None and not dto.space_ids:
        return SearchResponse(items=[])

    scope = await resolve_search_scope(organization_id, auth, grant_repository=grant_repository)

    if scope.is_empty:
        return SearchResponse(items=[])

    embedding = await embedder(dto.query)

    candidates = await search_index.search(
        query=dto.query,
        query_embedding=embedding,
        scope=scope,
        space_ids=dto.space_ids,
        options=SearchOptions(candidates_limit=min(dto.limit * 5, 200), max_hits_per_article=3),
    )
    if not candidates:
        return SearchResponse(items=[])

    # ВАЖНО: новый запрос к БД для защиты от Race Condition
    readable = {
        article.id: article
        for article in await article_query_repository.find_readable_published(
            organization_id,
            [candidate.article_id for candidate in candidates],
            subjects=({PUBLIC_SUBJECT} | build_subjects_from_auth(auth)) if auth is not None else {PUBLIC_SUBJECT},
            space_ids=dto.space_ids,
        )
    }

    items: list[SearchResult] = []

    for candidate in candidates:
        if (article := readable.get(candidate.article_id)) is None:
            continue

        hits = [hit for hit in candidate.hits if hit.revision_id == article.published_revision_id]
        if not hits:
            continue

        items.append(
            SearchResult(
                article=SearchArticle(
                    id=article.id,
                    space_id=article.space_id,
                    slug=article.slug,
                    title=article.title,
                    revision_id=article.published_revision_id,
                    published_at=article.published_at,
                ),
                score=candidate.score,
                fragments=[
                    SearchFragment(
                        chunk_id=hit.chunk_id,
                        text=hit.markdown,
                        heading_path=list(hit.heading_path),
                        anchor=hit.anchor,
                        score=hit.score,
                    )
                    for hit in hits
                ],
            )
        )

        if len(items) >= dto.limit:
            break

    return SearchResponse(items=items)
