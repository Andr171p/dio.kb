from fastapi import APIRouter, status

from src.api.dependencies.access import GrantRepositoryDep
from src.api.dependencies.articles import ArticleQueryRepositoryDep
from src.api.dependencies.auth import CurrentUser
from src.api.dependencies.search import SuggestionIndexDep, search_index, text_embedder
from src.application.search import usecases as search
from src.application.search.dtos import SearchRequest, SearchResponse, SuggestionRequest, SuggestionsResponse

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", status_code=status.HTTP_200_OK, summary="Поиск по опубликованным статьям")
async def search_articles(
    dto: SearchRequest,
    auth: CurrentUser,
    grant_repository: GrantRepositoryDep,
    article_query_repository: ArticleQueryRepositoryDep,
) -> SearchResponse:
    return await search.search_articles(
        auth.user.organization_id,
        auth,
        dto,
        grant_repository=grant_repository,
        article_query_repository=article_query_repository,
        search_index=search_index,
        embedder=text_embedder.embed_query,
    )


@router.post("/suggestions", status_code=status.HTTP_200_OK, summary="Подсказки по заголовкам")
async def suggest_articles(
    dto: SuggestionRequest,
    auth: CurrentUser,
    grant_repository: GrantRepositoryDep,
    article_query_repository: ArticleQueryRepositoryDep,
    suggestion_index: SuggestionIndexDep,
) -> SuggestionsResponse:
    return await search.suggest_articles(
        auth.user.organization_id,
        auth,
        dto,
        grant_repository=grant_repository,
        article_query_repository=article_query_repository,
        suggestion_index=suggestion_index,
    )
