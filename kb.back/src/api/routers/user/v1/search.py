from fastapi import APIRouter

from src.api.dependencies.auth import CurrentUser
from src.api.dependencies.repositories import ArticleQueryRepositoryDep, GrantRepositoryDep
from src.api.dependencies.search import ChunkRepositoryDep, EmbedderDep
from src.application.search import usecases
from src.application.search.dtos import SearchDTO, SearchResponse

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", summary="Поиск по опубликованным статьям")
async def search_articles(
    dto: SearchDTO,
    auth: CurrentUser,
    grant_repository: GrantRepositoryDep,
    article_query_repository: ArticleQueryRepositoryDep,
    chunk_repository: ChunkRepositoryDep,
    embedder: EmbedderDep,
) -> SearchResponse:
    return await usecases.search_articles(
        dto,
        auth,
        grant_repository=grant_repository,
        article_query_repository=article_query_repository,
        chunk_repository=chunk_repository,
        embedder=embedder,
    )
