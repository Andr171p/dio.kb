from ddf.infra.cache import InMemoryCache
from jwt import InvalidTokenError, decode
from mcp.server.auth.provider import AccessToken

from src.api.dependencies.auth import authenticate
from src.application.auth import Auth, AuthType, UnauthorizedError


class IamTokenVerifier:
    def __init__(self, *, resource: str) -> None:
        self._resource = resource
        self._cache = InMemoryCache[Auth]()

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            # IAM authenticates the original JWT. These claims only restrict its use by MCP.
            claims = decode(
                token,
                audience=self._resource,
                options={"verify_signature": False, "verify_aud": True, "verify_exp": True, "require": ["exp"]},
            )
            expires_at = int(claims["exp"])
        except InvalidTokenError, TypeError, OverflowError:
            return None

        try:
            auth = await authenticate(token, cache=self._cache)
        except UnauthorizedError:
            return None

        if auth.type is not AuthType.USER or auth.user is None:
            return None

        return AccessToken(
            token=token,
            client_id=str(auth.id),
            subject=str(auth.user.id),
            scopes=[],
            expires_at=expires_at,
            resource=self._resource,
            claims={"dios_auth": auth.model_dump(mode="json")},
        )
