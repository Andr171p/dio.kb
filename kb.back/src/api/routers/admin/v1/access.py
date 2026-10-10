from typing import Annotated

from uuid import UUID

from ddf.application.crud import Crud
from ddf.application.events import EventDispatcher
from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies.auth import CurrentAdmin
from src.api.dependencies.db import UnitOfWorkDep
from src.api.dependencies.repositories import GrantRepositoryDep
from src.application.access import usecases
from src.application.access.crud import (
    delete_access_grant_handler,
    delete_access_grant_wrapper,
    read_access_grant_wrapper,
    to_access_grant_response,
    update_access_grant_handler,
    update_access_grant_wrapper,
)
from src.application.access.dtos import (
    AccessGrantResponse,
    CreateAccessGrantDTO,
    ResourceType,
    UpdateAccessGrantDTO,
)
from src.application.auth import AuthUser
from src.domain.access.models import AccessGrant
from src.domain.access.vo import Resource

router = APIRouter(prefix="/access/grants", tags=["ACL"])

type AccessGrantCrud = Crud[
    AccessGrant,
    AccessGrantResponse,
    CreateAccessGrantDTO,
    UpdateAccessGrantDTO,
    AuthUser,
    AuthUser,
    AuthUser,
    AuthUser,
]


async def _publish_nothing(_: object) -> None:
    """У grants нет доменных событий: dispatcher используется только как владелец commit."""


def get_access_grant_crud(grant_repository: GrantRepositoryDep, uow: UnitOfWorkDep) -> AccessGrantCrud:
    return Crud(
        repository=grant_repository,
        dispatcher=EventDispatcher(uow, _publish_nothing),
        to_response=to_access_grant_response,
        update_handler=update_access_grant_handler,
        delete_handler=delete_access_grant_handler,
        read_wrapper=read_access_grant_wrapper,
        update_wrapper=update_access_grant_wrapper,
        delete_wrapper=delete_access_grant_wrapper,
    )


AccessGrantCrudDep = Annotated[AccessGrantCrud, Depends(get_access_grant_crud)]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Предоставить доступ")
async def create_access_grant(
    dto: CreateAccessGrantDTO,
    auth: CurrentAdmin,
    grant_repository: GrantRepositoryDep,
    uow: UnitOfWorkDep,
) -> AccessGrantResponse:
    return await usecases.grant_access(dto, auth, grant_repository=grant_repository, uow=uow)


@router.get("", summary="Доступы к ресурсу")
async def list_access_grants(
    resource_type: Annotated[ResourceType, Query(alias="resourceType")],
    resource_id: Annotated[UUID, Query(alias="resourceId")],
    auth: CurrentAdmin,
    grant_repository: GrantRepositoryDep,
) -> list[AccessGrantResponse]:
    return await usecases.list_resource_grants(
        Resource(type=resource_type, id=resource_id),
        auth,
        grant_repository=grant_repository,
    )


@router.get("/{grant_id}", summary="Получить информацию о доступе")
async def get_access_grant(
    grant_id: UUID, auth: CurrentAdmin, crud: AccessGrantCrudDep
) -> AccessGrantResponse:
    return await crud.read(grant_id, auth)


@router.patch("/{grant_id}", summary="Обновить права доступа")
async def update_access_grant(
    grant_id: UUID,
    dto: UpdateAccessGrantDTO,
    auth: CurrentAdmin,
    crud: AccessGrantCrudDep,
) -> AccessGrantResponse:
    return await crud.update(grant_id, dto, auth)


@router.delete("/{grant_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Отозвать доступ")
async def delete_access_grant(grant_id: UUID, auth: CurrentAdmin, crud: AccessGrantCrudDep) -> None:
    await crud.delete(grant_id, auth)
