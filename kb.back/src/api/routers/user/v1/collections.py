from uuid import UUID

from fastapi import APIRouter, status

from src.api.dependencies.access import GrantRepositoryDep
from src.api.dependencies.articles import ArticleRepositoryDep
from src.api.dependencies.auth import CurrentUser
from src.api.dependencies.collections import CollectionRepositoryDep, PlacementRepositoryDep
from src.api.dependencies.db import DBSession
from src.application.collections import usecases
from src.application.collections.dtos import (
    CollectionPlacementResponse,
    CollectionResponse,
    CreatePlacementDTO,
    UpdateCollectionDTO,
)

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.get("/{collection_id}", summary="Получить коллекцию")
async def get_collection(
    collection_id: UUID,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> CollectionResponse:
    return await usecases.get_collection(
        collection_id,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )


@router.patch("/{collection_id}", summary="Обновить коллекцию")
async def update_collection(
    collection_id: UUID,
    dto: UpdateCollectionDTO,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: DBSession,
) -> CollectionResponse:
    return await usecases.update_collection(
        collection_id,
        dto,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
        uow=uow,
    )


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Архивировать пустую коллекцию",
)
async def archive_collection(
    collection_id: UUID,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: DBSession,
) -> None:
    await usecases.archive_collection(
        collection_id,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
        uow=uow,
    )


@router.get("/{collection_id}/placements", summary="Элементы коллекции по порядку")
async def list_collection_placements(
    collection_id: UUID,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> list[CollectionPlacementResponse]:
    return await usecases.list_collection_placements(
        collection_id,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )


@router.post(
    "/{collection_id}/placements",
    status_code=status.HTTP_201_CREATED,
    summary="Разместить статью или коллекцию",
)
async def create_collection_placement(
    collection_id: UUID,
    dto: CreatePlacementDTO,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    article_repository: ArticleRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: DBSession,
) -> CollectionPlacementResponse:
    return await usecases.create_collection_placement(
        collection_id,
        dto,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        article_repository=article_repository,
        grant_repository=grant_repository,
        uow=uow,
    )
