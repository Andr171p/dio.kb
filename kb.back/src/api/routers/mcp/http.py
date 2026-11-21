"""ASGI wiring for embedding the MCP server in the FastAPI app."""

from urllib.parse import urlsplit

from mcp.server.auth.routes import create_protected_resource_routes
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.routing import Route

from .config import mcp_config
from .server import mcp

_resource = urlsplit(str(mcp_config.resource_url))

mcp_http_app: Starlette = mcp.streamable_http_app(
    streamable_http_path="/",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[_resource.netloc],
        allowed_origins=[f"{_resource.scheme}://{_resource.netloc}"],
    ),
)

# Mounted under `/api/mcp` the SDK's well-known route is unreachable at the RFC path;
# serve discovery on the host app at the origin instead.
oauth_protected_resource_routes: list[Route] = create_protected_resource_routes(
    resource_url=mcp_config.resource_url,
    authorization_servers=[mcp_config.issuer_url],
)
