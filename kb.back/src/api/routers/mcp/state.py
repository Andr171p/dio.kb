from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from src.api.dependencies.search import search_index, text_embedder
from src.application.search.indexes import SearchIndexReader
from src.application.search.types import TextEmbedder


@dataclass(frozen=True, slots=True)
class McpState:
    search_index: SearchIndexReader
    embedder: TextEmbedder


McpContext = Context[McpState]


@asynccontextmanager
async def mcp_lifespan(_: MCPServer[McpState]) -> AsyncIterator[McpState]:
    yield McpState(search_index=search_index, embedder=text_embedder.embed_query)
