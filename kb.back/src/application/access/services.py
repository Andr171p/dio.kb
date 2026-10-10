from collections.abc import Collection

from src.application.auth.dtos import AuthUser
from src.domain.access.logic import has_permission
from src.domain.access.types import Permission
from src.domain.access.vo import Resource, Subject

from .exceptions import AccessDeniedError
from .repositories import AccessGrantRepository


def build_subjects_from_auth(auth: AuthUser) -> frozenset[Subject]:
    """Множество субъектов, от имени которых действует доверенный пользователь."""

    user = auth.user
    return frozenset(
        {
            Subject(type="organization", id=str(user.organization_id)),
            Subject(type="user", id=str(user.id)),
            *(Subject(type="role", id=role) for role in user.roles),
        }
    )


async def resolve_permissions(
    auth: AuthUser,
    resources: Collection[Resource],
    *,
    grant_repository: AccessGrantRepository,
) -> Permission:
    """Эффективные (объединённые) права пользователя на набор ресурсов."""

    if not resources:
        return Permission(0)

    subjects = build_subjects_from_auth(auth)
    return await grant_repository.resolve_permission(auth.user.organization_id, resources, subjects)


async def ensure_access(
    auth: AuthUser,
    resources: Collection[Resource],
    required: Permission,
    *,
    grant_repository: AccessGrantRepository,
) -> None:
    """Проверяет, что объединённые права субъектов на ``resources`` покрывают ``required``."""

    if required == Permission(0):
        raise ValueError("Must be at least one required permission.")

    permissions = await resolve_permissions(auth, resources, grant_repository=grant_repository)

    if not has_permission(permissions, required):
        raise AccessDeniedError("Access denied.")
