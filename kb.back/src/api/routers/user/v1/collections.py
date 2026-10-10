from uuid import UUID

from fastapi import APIRouter, status

from src.api.dependencies.auth import CurrentUser
from src.api.dependencies.db import UnitOfWorkDep
from src.api.dependencies.repositories import (
    ArticleRepositoryDep,
    CollectionRepositoryDep,
    GrantRepositoryDep,
    PlacementRepositoryDep,
)
from src.application.collections import usecases
from src.application.collections.dtos import (
    CollectionPlacementResponse,
    CollectionResponse,
    CreatePlacementDTO,
    MovePlacementDTO,
    UpdateCollectionDTO,
)

router = APIRouter(tags=["Collections"])


@router.get("/collections/{collection_id}", summary="Получить коллекцию")
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


@router.patch("/collections/{collection_id}", summary="Обновить коллекцию")
async def update_collection(
    collection_id: UUID,
    dto: UpdateCollectionDTO,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: UnitOfWorkDep,
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
    "/collections/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Архивировать пустую коллекцию",
)
async def archive_collection(
    collection_id: UUID,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: UnitOfWorkDep,
) -> None:
    await usecases.archive_collection(
        collection_id,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
        uow=uow,
    )


@router.get("/collections/{collection_id}/placements", summary="Элементы коллекции по порядку")
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
    "/collections/{collection_id}/placements",
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
    uow: UnitOfWorkDep,
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


@router.patch("/placements/{placement_id}", summary="Переместить элемент")
async def move_collection_placement(
    placement_id: UUID,
    dto: MovePlacementDTO,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    article_repository: ArticleRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: UnitOfWorkDep,
) -> CollectionPlacementResponse:
    return await usecases.move_collection_placement(
        placement_id,
        dto,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        article_repository=article_repository,
        grant_repository=grant_repository,
        uow=uow,
    )


@router.delete(
    "/placements/{placement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Убрать элемент из коллекции",
)
async def delete_collection_placement(
    placement_id: UUID,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: UnitOfWorkDep,
) -> None:
    await usecases.delete_collection_placement(
        placement_id,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
        uow=uow,
    )
