from typing import Annotated

import hashlib
from collections.abc import Callable

from ddf.infra.cache import InMemoryCache
from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.auth.dtos import Auth, AuthType, AuthUser
from src.application.auth.exceptions import PermissionDeniedError, UnauthorizedError
from src.infra.services.iam import SrvIamClient, SrvIamConfig

_CACHE_TTL = 10 * 60

bearer_scheme = HTTPBearer(auto_error=False, description="Access токен DIOS")

iam_config = SrvIamConfig()  # type: ignore[call-arg]
iam_client = SrvIamClient(iam_config)


async def authenticate(token: str, *, cache: InMemoryCache[Auth]) -> Auth:
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

    return await authenticate(credentials.credentials, cache=request.app.state.auth_cache)


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


def get_current_client(auth: CurrentAuth) -> Auth:
    # Legacy: сервисных аккаунтов пока нет, service-to-service ходим под админом DIOS
    is_legacy_admin = auth.user is not None and AuthUser.model_validate(auth, from_attributes=True).is_admin
    if auth.type not in {AuthType.CLIENT, AuthType.ADMIN} and not is_legacy_admin:
        raise PermissionDeniedError("Service authentication required.")

    return auth


CurrentClient = Annotated[Auth, Depends(get_current_client)]


def require_auth_type(*required_types: AuthType) -> Callable[[Auth], Auth]:
    def dependency(auth: Annotated[Auth, Depends(get_current_auth)]) -> Auth:
        if auth.type not in required_types:
            raise PermissionDeniedError(f"Access denied for auth type: {auth.type.name!r}.")

        return auth

    return dependency


require_auth_user = Security(require_auth_type(AuthType.USER))

# Legacy: сервисных аккаунтов пока нет, service-to-service ходим под админом
require_auth_client = Security(require_auth_type(AuthType.CLIENT, AuthType.ADMIN))

__all__ = [
    "CurrentAdmin",
    "CurrentAuth",
    "CurrentClient",
    "CurrentUser",
    "authenticate",
    "get_current_client",
    "get_current_user",
    "iam_client",
    "require_auth_client",
    "require_auth_user",
]
