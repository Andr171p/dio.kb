from mcp.server import MCPServer
from mcp.server.auth.settings import AuthSettings
from mcp_types import ToolAnnotations

from .config import mcp_config
from .dependencies import with_db_session
from .state import mcp_lifespan
from .token_verifier import IamTokenVerifier
from .tools import get_article, get_spaces, search_knowledge

mcp = MCPServer(
    "DIOS Knowledge Base",
    lifespan=mcp_lifespan,
    middleware=[with_db_session],
    auth=AuthSettings(
        issuer_url=mcp_config.issuer_url,
        resource_server_url=mcp_config.resource_url,
        validate_token_resource=True,
    ),
    token_verifier=IamTokenVerifier(resource=str(mcp_config.resource_url)),
)

read_only = ToolAnnotations(read_only_hint=True, open_world_hint=False)
mcp.add_tool(search_knowledge, annotations=read_only)
mcp.add_tool(get_article, annotations=read_only)
mcp.add_tool(get_spaces, annotations=read_only)
