from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from ddf.application.exceptions import NotFoundError

from src.application.auth.dtos import AuthUser
from src.domain.access.models import AccessGrant

from .dtos import AccessGrantResponse, UpdateAccessGrantDTO


def _ensure_visible(grant: AccessGrant, auth: AuthUser | None) -> None:
    if auth is None or grant.is_deleted or grant.organization_id != auth.user.organization_id:
        raise NotFoundError(f"Access grant with ID {grant.id} not found.")


async def read_access_grant_wrapper(
    base: Callable[[AccessGrant, AuthUser | None], Awaitable[AccessGrant]],
    grant: AccessGrant,
    auth: AuthUser | None,
) -> AccessGrant:
    _ensure_visible(grant, auth)
    return await base(grant, auth)


async def update_access_grant_wrapper(
    base: Callable[[AccessGrant, UpdateAccessGrantDTO, AuthUser | None], Awaitable[AccessGrant]],
    grant: AccessGrant,
    dto: UpdateAccessGrantDTO,
    auth: AuthUser | None,
) -> AccessGrant:
    _ensure_visible(grant, auth)
    return await base(grant, dto, auth)


async def delete_access_grant_wrapper(
    base: Callable[[AccessGrant, AuthUser | None], Awaitable[AccessGrant]],
    grant: AccessGrant,
    auth: AuthUser | None,
) -> AccessGrant:
    _ensure_visible(grant, auth)
    return await base(grant, auth)


async def update_access_grant_handler(
    grant: AccessGrant,
    dto: UpdateAccessGrantDTO,
    _: AuthUser | None = None,
) -> AccessGrant:
    grant.permissions = dto.permissions
    grant.updated_at = datetime.now(UTC)
    return grant


async def delete_access_grant_handler(grant: AccessGrant, _: AuthUser | None = None) -> AccessGrant:
    grant.deleted_at = grant.updated_at = datetime.now(UTC)
    return grant


def to_access_grant_response(grant: AccessGrant) -> AccessGrantResponse:
    return AccessGrantResponse.model_validate(grant)


__all__ = [
    "delete_access_grant_handler",
    "delete_access_grant_wrapper",
    "read_access_grant_wrapper",
    "to_access_grant_response",
    "update_access_grant_handler",
    "update_access_grant_wrapper",
]
