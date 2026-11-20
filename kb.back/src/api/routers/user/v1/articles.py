from uuid import UUID

from fastapi import APIRouter, status

from src.api.dependencies.access import GrantRepositoryDep
from src.api.dependencies.articles import ArticleRepositoryDep, RevisionRepositoryDep
from src.api.dependencies.auth import CurrentUser
from src.api.dependencies.db import DBSession, OutboxDep
from src.application.articles import usecases
from src.application.articles.dtos import (
    ArticleDetailResponse,
    ArticleResponse,
    ArticleRevisionResponse,
    ArticleRevisionSummaryResponse,
    PublishArticleDTO,
    RestoreArticleRevisionDTO,
    ReviseArticleDTO,
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
    return await usecases.get_published_article(
        article_id,
        auth,
        article_repository=article_repository,
        revision_repository=revision_repository,
        grant_repository=grant_repository,
    )


@router.get(
    "/{article_id}/draft",
    status_code=status.HTTP_200_OK,
    summary="Текущая (редакторская) версия статьи",
)
async def get_article_draft(
    article_id: UUID,
    auth: CurrentUser,
    article_repository: ArticleRepositoryDep,
    revision_repository: RevisionRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> ArticleDetailResponse:
    return await usecases.get_article_draft(
        article_id,
        auth,
        article_repository=article_repository,
        revision_repository=revision_repository,
        grant_repository=grant_repository,
    )


@router.post(
    "/{article_id}/revisions",
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую редакцию статьи",
)
async def revise_article(
    article_id: UUID,
    dto: ReviseArticleDTO,
    auth: CurrentUser,
    article_repository: ArticleRepositoryDep,
    revision_repository: RevisionRepositoryDep,
    grant_repository: GrantRepositoryDep,
    db: DBSession,
) -> ArticleDetailResponse:
    return await usecases.revise_article(
        article_id,
        dto,
        auth,
        article_repository=article_repository,
        revision_repository=revision_repository,
        grant_repository=grant_repository,
        uow=db,
    )


@router.get(
    "/{article_id}/revisions",
    status_code=status.HTTP_200_OK,
    summary="История редакций",
)
async def list_article_revisions(
    article_id: UUID,
    auth: CurrentUser,
    article_repository: ArticleRepositoryDep,
    revision_repository: RevisionRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> list[ArticleRevisionSummaryResponse]:
    return await usecases.list_article_revisions(
        article_id,
        auth,
        article_repository=article_repository,
        revision_repository=revision_repository,
        grant_repository=grant_repository,
    )


@router.get(
    "/{article_id}/revisions/{revision_id}",
    status_code=status.HTTP_200_OK,
    summary="Получить редакцию",
)
async def get_article_revision(
    article_id: UUID,
    revision_id: UUID,
    auth: CurrentUser,
    article_repository: ArticleRepositoryDep,
    revision_repository: RevisionRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> ArticleRevisionResponse:
    return await usecases.get_article_revision(
        article_id,
        revision_id,
        auth,
        article_repository=article_repository,
        revision_repository=revision_repository,
        grant_repository=grant_repository,
    )


@router.post(
    "/{article_id}/revisions/{revision_id}/restore",
    status_code=status.HTTP_201_CREATED,
    summary="Восстановить историческую редакцию (создаёт новую)",
)
async def restore_article_revision(
    article_id: UUID,
    revision_id: UUID,
    dto: RestoreArticleRevisionDTO,
    auth: CurrentUser,
    article_repository: ArticleRepositoryDep,
    revision_repository: RevisionRepositoryDep,
    grant_repository: GrantRepositoryDep,
    db: DBSession,
) -> ArticleDetailResponse:
    return await usecases.restore_article_revision(
        article_id,
        revision_id,
        dto,
        auth,
        article_repository=article_repository,
        revision_repository=revision_repository,
        grant_repository=grant_repository,
        uow=db,
    )


@router.post(
    "/{article_id}/publish",
    status_code=status.HTTP_200_OK,
    summary="Опубликовать текущую редакцию",
)
async def publish_article(
    article_id: UUID,
    dto: PublishArticleDTO,
    auth: CurrentUser,
    article_repository: ArticleRepositoryDep,
    grant_repository: GrantRepositoryDep,
    outbox: OutboxDep,
    db: DBSession,
) -> ArticleResponse:
    return await usecases.publish_article(
        article_id,
        dto,
        auth,
        article_repository=article_repository,
        grant_repository=grant_repository,
        outbox=outbox,
        uow=db,
    )


@router.post(
    "/{article_id}/unpublish",
    status_code=status.HTTP_200_OK,
    summary="Снять с публикации",
)
async def unpublish_article(
    article_id: UUID,
    auth: CurrentUser,
    article_repository: ArticleRepositoryDep,
    grant_repository: GrantRepositoryDep,
    outbox: OutboxDep,
    db: DBSession,
) -> ArticleResponse:
    return await usecases.unpublish_article(
        article_id,
        auth,
        article_repository=article_repository,
        grant_repository=grant_repository,
        outbox=outbox,
        uow=db,
    )


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Архивировать статью")
async def archive_article(
    article_id: UUID,
    auth: CurrentUser,
    article_repository: ArticleRepositoryDep,
    grant_repository: GrantRepositoryDep,
    outbox: OutboxDep,
    db: DBSession,
) -> None:
    await usecases.archive_article(
        article_id,
        auth,
        article_repository=article_repository,
        grant_repository=grant_repository,
        outbox=outbox,
        uow=db,
    )


@router.post(
    "/{article_id}/restore",
    status_code=status.HTTP_200_OK,
    summary="Вернуть статью из архива (черновиком)",
)
async def restore_article(
    article_id: UUID,
    auth: CurrentUser,
    article_repository: ArticleRepositoryDep,
    grant_repository: GrantRepositoryDep,
    db: DBSession,
) -> ArticleResponse:
    return await usecases.restore_article(
        article_id,
        auth,
        article_repository=article_repository,
        grant_repository=grant_repository,
        uow=db,
    )
