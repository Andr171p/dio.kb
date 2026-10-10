from collections.abc import Collection
from uuid import UUID

from src.application.access import AccessGrantRepository, Permission, build_subjects_from_auth
from src.application.articles.repositories import ArticleQueryRepository
from src.application.auth import AuthUser, PermissionDeniedError

from .dtos import (
    SearchArticleResponse,
    SearchDTO,
    SearchFragmentResponse,
    SearchResponse,
    SearchResultResponse,
    SyncQueuedResponse,
)
from .models import SearchScope
from .protocols import IndexingQueue, TextEmbedder
from .repositories import ArticleIndexStateRepository, SearchChunkRepository

_OVERFETCH_FACTOR = 2
_HITS_PER_ARTICLE = 3


async def resolve_search_scope(
    auth: AuthUser,
    space_ids: Collection[UUID] | None = None,
    *,
    grant_repository: AccessGrantRepository,
) -> SearchScope:
    """READ-область пользователя: пространства с READ и статьи с прямым READ."""

    organization_id = auth.user.organization_id
    subjects = build_subjects_from_auth(auth)

    readable_space_ids = frozenset(
        await grant_repository.find_resource_ids(organization_id, subjects, "space", Permission.READ),
    )
    readable_article_ids = frozenset(
        await grant_repository.find_resource_ids(organization_id, subjects, "article", Permission.READ),
    )

    if space_ids is None:
        return SearchScope(space_ids=readable_space_ids, article_ids=readable_article_ids)

    restrict_space_ids = frozenset(space_ids)
    return SearchScope(
        space_ids=readable_space_ids & restrict_space_ids,
        article_ids=readable_article_ids,
        restrict_space_ids=restrict_space_ids,
    )


async def search_articles(
    dto: SearchDTO,
    auth: AuthUser,
    *,
    grant_repository: AccessGrantRepository,
    article_query_repository: ArticleQueryRepository,
    chunk_repository: SearchChunkRepository,
    embedder: TextEmbedder,
) -> SearchResponse:
    """
    Безопасный гибридный поиск по опубликованным статьям.

    1. Область поиска вычисляется до обращения к индексу; пустая — пустой ответ без запроса.
    2. Индекс ищет только внутри области (фильтр по организации, Space и статьям).
    3. Кандидаты сверяются с PostgreSQL: публикация, актуальная редакция, архив, область —
       только после этого фрагменты попадают в ответ.
    """

    scope = await resolve_search_scope(auth, dto.space_ids, grant_repository=grant_repository)
    if scope.is_empty:
        return SearchResponse(items=[])

    query_vector = await embedder.embed_query(dto.query)
    candidates = await chunk_repository.search(
        query=dto.query,
        query_vector=query_vector,
        organization_id=auth.user.organization_id,
        scope=scope,
        limit=dto.limit * _OVERFETCH_FACTOR,
        hits_per_article=_HITS_PER_ARTICLE,
    )
    if not candidates:
        return SearchResponse(items=[])

    published = {
        article.id: article
        for article in await article_query_repository.find_published(
            auth.user.organization_id,
            [candidate.article_id for candidate in candidates],
        )
    }

    items: list[SearchResultResponse] = []
    for candidate in candidates:
        article = published.get(candidate.article_id)
        if article is None or not scope.allows(article.id, article.space_id):
            continue

        hits = [hit for hit in candidate.hits if hit.revision_id == article.published_revision_id]
        if not hits:
            continue

        items.append(
            SearchResultResponse(
                article=SearchArticleResponse(
                    id=article.id,
                    space_id=article.space_id,
                    slug=article.slug,
                    title=article.title,
                    revision_id=article.published_revision_id,
                    published_at=article.published_at,
                ),
                score=candidate.score,
                fragments=[
                    SearchFragmentResponse(
                        chunk_id=hit.chunk_id,
                        text=hit.text,
                        heading_path=list(hit.heading_path),
                        anchor=hit.anchor,
                        score=hit.score,
                    )
                    for hit in hits
                ],
            )
        )
        if len(items) == dto.limit:
            break

    return SearchResponse(items=items)


async def request_article_reindex(
    article_id: UUID,
    auth: AuthUser,
    *,
    indexing_queue: IndexingQueue,
) -> SyncQueuedResponse:
    if not auth.is_admin:
        raise PermissionDeniedError("Only administrators can manage the search index.")

    await indexing_queue.enqueue_article(article_id)
    return SyncQueuedResponse(queued=1)


async def reconcile_search_index(
    auth: AuthUser,
    *,
    index_state_repository: ArticleIndexStateRepository,
    chunk_repository: SearchChunkRepository,
    indexing_queue: IndexingQueue,
    full: bool = False,
) -> SyncQueuedResponse:
    """
    Ставит в очередь статьи, чьё состояние в индексе расходится с PostgreSQL (и после смены индекса).

    ``full`` — переиндексировать всё, что должно быть в индексе или могло в нём остаться:
    нужно, если сам индекс потерян или пересоздан вне приложения.
    """

    if not auth.is_admin:
        raise PermissionDeniedError("Only administrators can manage the search index.")

    article_ids = await index_state_repository.find_out_of_sync_article_ids(
        chunk_repository.index_name, full=full
    )
    for article_id in article_ids:
        await indexing_queue.enqueue_article(article_id)

    return SyncQueuedResponse(queued=len(article_ids))
