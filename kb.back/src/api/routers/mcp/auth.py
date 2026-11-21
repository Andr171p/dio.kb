from typing import Annotated

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.mcpserver import Resolve
from mcp.server.mcpserver.exceptions import ToolError

from src.api.dependencies.auth import get_current_user
from src.application.auth import Auth, AuthUser, PermissionDeniedError


def get_current_mcp_auth() -> Auth:
    """Возвращает IAM-идентичность, проверенную MCP auth middleware."""

    token = get_access_token()
    if token is None or token.claims is None or (auth_data := token.claims.get("dios_auth")) is None:
        raise ToolError("User authentication required.")
    return Auth.model_validate(auth_data)


CurrentMcpAuth = Annotated[Auth, Resolve(get_current_mcp_auth)]


def require_mcp_user(auth: CurrentMcpAuth) -> AuthUser:
    try:
        return get_current_user(auth)
    except PermissionDeniedError as exc:
        raise ToolError("User authentication required.") from exc


CurrentMcpUser = Annotated[AuthUser, Resolve(require_mcp_user)]

__all__ = ["CurrentMcpAuth", "CurrentMcpUser"]
