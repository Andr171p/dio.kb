from typing import Annotated

from fastapi import Depends

from src.api.dependencies.db import DBSession
from src.application.collections.repositories import CollectionPlacementRepository, CollectionRepository
from src.infra.database.repositories import SqlAlchemyCollectionPlacementRepository, SqlAlchemyCollectionRepository


def get_collection_repository(session: DBSession) -> CollectionRepository:
    return SqlAlchemyCollectionRepository(session)


def get_placement_repository(session: DBSession) -> CollectionPlacementRepository:
    return SqlAlchemyCollectionPlacementRepository(session)


CollectionRepositoryDep = Annotated[CollectionRepository, Depends(get_collection_repository)]
PlacementRepositoryDep = Annotated[CollectionPlacementRepository, Depends(get_placement_repository)]

__all__ = ["CollectionRepositoryDep", "PlacementRepositoryDep"]
