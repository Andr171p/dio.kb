from datetime import UTC, datetime
from uuid import UUID

from ddf.application.uow import UnitOfWork

from src.application.access import (
    AccessGrantRepository,
    Permission,
    Resource,
    Subject,
    build_subjects_from_auth,
)
from src.application.auth import AuthUser, PermissionDeniedError
from src.domain.access.models import AccessGrant
from src.domain.spaces.models import Space

from .access import get_accessible_space
from .dtos import CreateSpaceDTO, SpaceResponse, UpdateSpaceDTO
from .repositories import SpaceRepository

_OWNER_PERMISSIONS = Permission.READ | Permission.WRITE | Permission.PUBLISH | Permission.ARCHIVE


async def create_space(
    dto: CreateSpaceDTO,
    auth: AuthUser,
    *,
    space_repository: SpaceRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> SpaceResponse:
    """Создаёт пространство: создатель получает полные права, опционально READ для всей организации."""

    if not auth.is_admin:
        raise PermissionDeniedError("Only administrators can create spaces.")

    organization_id = auth.user.organization_id
    space = Space(
        organization_id=organization_id,
        key=dto.key,
        name=dto.name,
        description=dto.description,
        created_by=auth.user.id,
    )
    resource = Resource(type="space", id=space.id)

    grants = [
        AccessGrant(
            organization_id=organization_id,
            granted_by=auth.user.id,
            resource=resource,
            subject=Subject(type="user", id=str(auth.user.id)),
            permissions=_OWNER_PERMISSIONS,
        ),
    ]
    if dto.organization_wide:
        grants.append(
            AccessGrant(
                organization_id=organization_id,
                granted_by=auth.user.id,
                resource=resource,
                subject=Subject(type="organization", id=str(organization_id)),
                permissions=Permission.READ,
            )
        )

    await space_repository.create(space)
    for grant in grants:
        await grant_repository.create(grant)

    await uow.commit()
    return SpaceResponse.model_validate(space)


async def list_spaces(
    auth: AuthUser,
    *,
    space_repository: SpaceRepository,
    grant_repository: AccessGrantRepository,
) -> list[SpaceResponse]:
    """Пространства, доступные пользователю на чтение."""

    space_ids = await grant_repository.find_resource_ids(
        auth.user.organization_id,
        build_subjects_from_auth(auth),
        "space",
        Permission.READ,
    )
    spaces = await space_repository.get_by_ids(list(space_ids)) if space_ids else ()

    return [
        SpaceResponse.model_validate(space)
        for space in sorted(spaces, key=lambda space: space.name)
        if not space.is_deleted and space.organization_id == auth.user.organization_id
    ]


async def get_space(
    space_id: UUID,
    auth: AuthUser,
    *,
    space_repository: SpaceRepository,
    grant_repository: AccessGrantRepository,
) -> SpaceResponse:
    space = await get_accessible_space(
        space_id,
        auth,
        Permission.READ,
        space_repository=space_repository,
        grant_repository=grant_repository,
    )
    return SpaceResponse.model_validate(space)


async def update_space(
    space_id: UUID,
    dto: UpdateSpaceDTO,
    auth: AuthUser,
    *,
    space_repository: SpaceRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> SpaceResponse:
    space = await get_accessible_space(
        space_id,
        auth,
        Permission.WRITE,
        space_repository=space_repository,
        grant_repository=grant_repository,
    )

    if dto.name is not None:
        space.name = dto.name
    if "description" in dto.model_fields_set:
        space.description = dto.description or None

    space.updated_at = datetime.now(UTC)
    await space_repository.update(space)
    await uow.commit()

    return SpaceResponse.model_validate(space)


async def archive_space(
    space_id: UUID,
    auth: AuthUser,
    *,
    space_repository: SpaceRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> None:
    """Архивирует пространство; его статьи перестают выдаваться в поиске сразу по данным PostgreSQL."""

    space = await get_accessible_space(
        space_id,
        auth,
        Permission.ARCHIVE,
        space_repository=space_repository,
        grant_repository=grant_repository,
    )
    space.deleted_at = space.updated_at = datetime.now(UTC)
    await space_repository.update(space)
    await uow.commit()
