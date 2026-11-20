from uuid import UUID

from fastapi import APIRouter, status

from src.api.dependencies.access import GrantRepositoryDep
from src.api.dependencies.articles import ArticleRepositoryDep
from src.api.dependencies.auth import CurrentUser
from src.api.dependencies.collections import CollectionRepositoryDep, PlacementRepositoryDep
from src.api.dependencies.db import DBSession
from src.application.collections import usecases as placements
from src.application.collections.dtos import CollectionPlacementResponse, MovePlacementDTO

router = APIRouter(prefix="/collection-placements", tags=["Collection Placements"])


@router.patch("/placements/{placement_id}", summary="Переместить элемент")
async def move_collection_placement(
    placement_id: UUID,
    dto: MovePlacementDTO,
    auth: CurrentUser,
    collection_repository: CollectionRepositoryDep,
    placement_repository: PlacementRepositoryDep,
    article_repository: ArticleRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: DBSession,
) -> CollectionPlacementResponse:
    return await placements.move_collection_placement(
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
    uow: DBSession,
) -> None:
    await placements.delete_collection_placement(
        placement_id,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
        uow=uow,
    )
