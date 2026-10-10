from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Query, status

from src.api.dependencies.auth import CurrentAdmin
from src.api.dependencies.repositories import IndexStateRepositoryDep
from src.api.dependencies.search import ChunkRepositoryDep, IndexingQueueDep
from src.application.search import usecases
from src.application.search.dtos import SyncQueuedResponse

router = APIRouter(prefix="/search", tags=["Search index"])


@router.post(
    "/articles/{article_id}/sync",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Переиндексировать статью",
)
async def sync_article(
    article_id: UUID, auth: CurrentAdmin, indexing_queue: IndexingQueueDep
) -> SyncQueuedResponse:
    return await usecases.request_article_reindex(article_id, auth, indexing_queue=indexing_queue)


@router.post(
    "/reconcile",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Синхронизировать индекс с PostgreSQL (расхождения, новое поколение индекса)",
)
async def reconcile_index(
    auth: CurrentAdmin,
    index_state_repository: IndexStateRepositoryDep,
    chunk_repository: ChunkRepositoryDep,
    indexing_queue: IndexingQueueDep,
    full: Annotated[bool, Query(description="Переиндексировать все статьи (индекс потерян)")] = False,
) -> SyncQueuedResponse:
    return await usecases.reconcile_search_index(
        auth,
        index_state_repository=index_state_repository,
        chunk_repository=chunk_repository,
        indexing_queue=indexing_queue,
        full=full,
    )
