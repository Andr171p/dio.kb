from uuid import UUID

from fastapi import APIRouter, status

from src.api.dependencies.auth import CurrentUser
from src.api.dependencies.db import UnitOfWorkDep
from src.api.dependencies.repositories import (
    ArticleQueryRepositoryDep,
    ArticleRepositoryDep,
    CollectionRepositoryDep,
    GrantRepositoryDep,
    PlacementRepositoryDep,
    RevisionRepositoryDep,
    SpaceRepositoryDep,
)
from src.application.articles import usecases as articles
from src.application.articles.dtos import ArticleDetailResponse, ArticleSummaryResponse, CreateArticleDTO
from src.application.collections import usecases as collections
from src.application.collections.dtos import CollectionResponse, CreateCollectionDTO, SpaceNavigationResponse
from src.application.spaces import usecases as spaces
from src.application.spaces.dtos import SpaceResponse, UpdateSpaceDTO

router = APIRouter(prefix="/spaces", tags=["Spaces"])


@router.get("", summary="Доступные пространства")
async def list_spaces(
    auth: CurrentUser,
    space_repository: SpaceRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> list[SpaceResponse]:
    return await spaces.list_spaces(
        auth, space_repository=space_repository, grant_repository=grant_repository
    )


@router.get("/{space_id}", summary="Получить пространство")
async def get_space(
    space_id: UUID,
    auth: CurrentUser,
    space_repository: SpaceRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> SpaceResponse:
    return await spaces.get_space(
        space_id,
        auth,
        space_repository=space_repository,
        grant_repository=grant_repository,
    )


@router.patch("/{space_id}", summary="Обновить пространство")
async def update_space(
    space_id: UUID,
    dto: UpdateSpaceDTO,
    auth: CurrentUser,
    space_repository: SpaceRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: UnitOfWorkDep,
) -> SpaceResponse:
    return await spaces.update_space(
        space_id,
        dto,
        auth,
        space_repository=space_repository,
        grant_repository=grant_repository,
        uow=uow,
    )


@router.delete("/{space_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Архивировать пространство")
async def archive_space(
    space_id: UUID,
    auth: CurrentUser,
    space_repository: SpaceRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: UnitOfWorkDep,
) -> None:
    await spaces.archive_space(
        space_id,
        auth,
        space_repository=space_repository,
        grant_repository=grant_repository,
        uow=uow,
    )


@router.get("/{space_id}/navigation", summary="Дерево навигации пространства")
async def get_space_navigation(
    space_id: UUID,
    auth: CurrentUser,
    space_repository: SpaceRepositoryDep,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    article_query_repository: ArticleQueryRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> SpaceNavigationResponse:
    return await collections.get_space_navigation(
        space_id,
        auth,
        space_repository=space_repository,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        article_query_repository=article_query_repository,
        grant_repository=grant_repository,
    )


@router.post(
    "/{space_id}/collections",
    status_code=status.HTTP_201_CREATED,
    summary="Создать коллекцию",
)
async def create_collection(
    space_id: UUID,
    dto: CreateCollectionDTO,
    auth: CurrentUser,
    space_repository: SpaceRepositoryDep,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    article_repository: ArticleRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: UnitOfWorkDep,
) -> CollectionResponse:
    return await collections.create_collection(
        space_id,
        dto,
        auth,
        space_repository=space_repository,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        article_repository=article_repository,
        grant_repository=grant_repository,
        uow=uow,
    )


@router.get("/{space_id}/articles", summary="Статьи пространства")
async def list_space_articles(
    space_id: UUID,
    auth: CurrentUser,
    space_repository: SpaceRepositoryDep,
    article_query_repository: ArticleQueryRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> list[ArticleSummaryResponse]:
    return await articles.list_space_articles(
        space_id,
        auth,
        space_repository=space_repository,
        article_query_repository=article_query_repository,
        grant_repository=grant_repository,
    )


@router.post(
    "/{space_id}/articles",
    status_code=status.HTTP_201_CREATED,
    summary="Создать статью (черновик с первой редакцией)",
)
async def create_article(
    space_id: UUID,
    dto: CreateArticleDTO,
    auth: CurrentUser,
    space_repository: SpaceRepositoryDep,
    article_repository: ArticleRepositoryDep,
    revision_repository: RevisionRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: UnitOfWorkDep,
) -> ArticleDetailResponse:
    return await articles.create_article(
        space_id,
        dto,
        auth,
        space_repository=space_repository,
        article_repository=article_repository,
        revision_repository=revision_repository,
        grant_repository=grant_repository,
        uow=uow,
    )


@router.get("/{space_id}/articles/{slug}", summary="Опубликованная статья по slug")
async def get_published_article_by_slug(
    space_id: UUID,
    slug: str,
    auth: CurrentUser,
    article_repository: ArticleRepositoryDep,
    revision_repository: RevisionRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> ArticleDetailResponse:
    return await articles.get_published_article_by_slug(
        space_id,
        slug,
        auth,
        article_repository=article_repository,
        revision_repository=revision_repository,
        grant_repository=grant_repository,
    )
