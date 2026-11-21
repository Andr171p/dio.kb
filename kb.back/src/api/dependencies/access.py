from typing import Annotated

from fastapi import Depends

from src.api.dependencies.db import DBSession
from src.application.access.repositories import AccessGrantRepository
from src.infra.database.repositories import SqlAlchemyAccessGrantRepository


def get_grant_repository(session: DBSession) -> AccessGrantRepository:
    return SqlAlchemyAccessGrantRepository(session)


GrantRepositoryDep = Annotated[AccessGrantRepository, Depends(get_grant_repository)]
