from typing import Annotated

import hashlib

from ddf.infra.cache import InMemoryCache
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.auth.dtos import Auth, AuthType, AuthUser
from src.application.auth.exceptions import PermissionDeniedError, UnauthorizedError
from src.infra.services.iam import SrvIamClient

_CACHE_TTL = 10 * 60

bearer_scheme = HTTPBearer(auto_error=False, description="Access токен DIOS")


async def authenticate(token: str, *, iam_client: SrvIamClient, cache: InMemoryCache[Auth]) -> Auth:
    """Аутентифицирует access токен DIOS (с кэшем), общая точка для HTTP и MCP."""

    cache_key = f"iam:auth:{hashlib.sha256(token.encode()).hexdigest()}"

    if (cached_auth := await cache.get(cache_key)) is not None:
        return cached_auth

    auth = await iam_client.authenticate(token)
    await cache.set(cache_key, auth, ttl=_CACHE_TTL)
    return auth


async def get_current_auth(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> Auth:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Missing or invalid credentials.")

    return await authenticate(
        credentials.credentials,
        iam_client=request.app.state.iam_client,
        cache=request.app.state.auth_cache,
    )


CurrentAuth = Annotated[Auth, Depends(get_current_auth)]


def get_current_user(auth: CurrentAuth) -> AuthUser:
    if auth.type is not AuthType.USER or auth.user is None:
        raise PermissionDeniedError("User authentication required.")

    return AuthUser.model_validate(auth, from_attributes=True)


CurrentUser = Annotated[AuthUser, Depends(get_current_user)]


def get_current_admin(user: CurrentUser) -> AuthUser:
    if not user.is_admin:
        raise PermissionDeniedError("Administrator role required.")

    return user


CurrentAdmin = Annotated[AuthUser, Depends(get_current_admin)]


def get_current_service(auth: CurrentAuth) -> Auth:
    # Legacy: сервисных аккаунтов пока нет, service-to-service ходим под админом DIOS
    is_legacy_admin = auth.user is not None and AuthUser.model_validate(auth, from_attributes=True).is_admin
    if auth.type is not AuthType.SERVICE and not is_legacy_admin:
        raise PermissionDeniedError("Service authentication required.")

    return auth


CurrentService = Annotated[Auth, Depends(get_current_service)]

__all__ = ["CurrentAdmin", "CurrentAuth", "CurrentService", "CurrentUser", "authenticate"]
