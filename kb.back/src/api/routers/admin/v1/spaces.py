from fastapi import APIRouter, status

from src.api.dependencies.auth import CurrentAdmin
from src.api.dependencies.db import UnitOfWorkDep
from src.api.dependencies.repositories import GrantRepositoryDep, SpaceRepositoryDep
from src.application.spaces import usecases
from src.application.spaces.dtos import CreateSpaceDTO, SpaceResponse

router = APIRouter(prefix="/spaces", tags=["Spaces"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Создать пространство")
async def create_space(
    dto: CreateSpaceDTO,
    auth: CurrentAdmin,
    space_repository: SpaceRepositoryDep,
    grant_repository: GrantRepositoryDep,
    uow: UnitOfWorkDep,
) -> SpaceResponse:
    return await usecases.create_space(
        dto,
        auth,
        space_repository=space_repository,
        grant_repository=grant_repository,
        uow=uow,
    )
