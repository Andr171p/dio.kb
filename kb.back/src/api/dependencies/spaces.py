from typing import Annotated

from fastapi import Depends

from src.api.dependencies.db import DBSession
from src.application.spaces.repositories import SpaceRepository
from src.infra.database.repositories import SqlAlchemySpaceRepository


def get_space_repository(session: DBSession) -> SpaceRepository:
    return SqlAlchemySpaceRepository(session)


SpaceRepositoryDep = Annotated[SpaceRepository, Depends(get_space_repository)]
