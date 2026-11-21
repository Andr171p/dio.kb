from uuid import UUID

from fastapi import APIRouter, status

from src.api.dependencies.access import GrantRepositoryDep
from src.api.dependencies.articles import ArticleRepositoryDep, RevisionRepositoryDep
from src.api.dependencies.auth import CurrentUser
from src.application.articles import usecases as articles
from src.application.articles.dtos import (
    ArticleDetailResponse,
)

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get(
    "/{article_id}",
    status_code=status.HTTP_200_OK,
    summary="Опубликованная редакция статьи",
)
async def get_published_article(
    article_id: UUID,
    auth: CurrentUser,
    article_repository: ArticleRepositoryDep,
    revision_repository: RevisionRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> ArticleDetailResponse:
    return await articles.get_published_article(
        article_id,
        auth,
        article_repository=article_repository,
        revision_repository=revision_repository,
        grant_repository=grant_repository,
    )
