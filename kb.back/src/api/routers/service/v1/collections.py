from uuid import UUID

from fastapi import APIRouter, status

from src.api.dependencies.access import GrantRepositoryDep
from src.api.dependencies.auth import CurrentUser
from src.api.dependencies.collections import CollectionRepositoryDep, PlacementRepositoryDep
from src.application.collections import usecases as collections
from src.application.collections.dtos import (
    CollectionPlacementResponse,
    CollectionResponse,
)

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.get("/{collection_id}", summary="Получить коллекцию", status_code=status.HTTP_200_OK)
async def get_collection(
    collection_id: UUID,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> CollectionResponse:
    return await collections.get_collection(
        collection_id,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )


@router.get("/{collection_id}/placements", summary="Элементы коллекции по порядку", status_code=status.HTTP_200_OK)
async def list_collection_placements(
    collection_id: UUID,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    grant_repository: GrantRepositoryDep,
) -> list[CollectionPlacementResponse]:
    return await collections.list_collection_placements(
        collection_id,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )
