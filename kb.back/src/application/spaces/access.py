from uuid import UUID

from ddf.application.exceptions import NotFoundError

from src.application.access import AccessGrantRepository, Permission, Resource, ensure_access
from src.application.auth.dtos import AuthUser
from src.domain.spaces.models import Space

from .repositories import SpaceRepository


async def get_accessible_space(
    space_id: UUID,
    auth: AuthUser,
    required: Permission,
    *,
    space_repository: SpaceRepository,
    grant_repository: AccessGrantRepository,
) -> Space:
    """Загружает активное пространство организации пользователя и проверяет права на него."""

    space = await space_repository.read(space_id)

    if space is None or space.is_deleted or space.organization_id != auth.user.organization_id:
        raise NotFoundError(f"Space with ID {space_id} not found.")

    await ensure_access(
        auth, (Resource(type="space", id=space.id),), required, grant_repository=grant_repository
    )
    return space


__all__ = ["get_accessible_space"]
