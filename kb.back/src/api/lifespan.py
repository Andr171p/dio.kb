from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ddf.infra.cache import InMemoryCache
from fastapi import FastAPI
from mcp.server import MCPServer

from src.api.dependencies.auth import iam_client
from src.api.dependencies.db import engine
from src.api.dependencies.links import link_preview_fetcher
from src.api.dependencies.search import search_index, text_embedder
from src.application.auth import Auth
from src.infra.broker.broker import broker


@asynccontextmanager
async def lifespan(app: FastAPI, *, mcp: MCPServer) -> AsyncIterator[None]:
    # noinspection PyUnresolvedReferences
    app.state.iam_client = iam_client
    # noinspection PyUnresolvedReferences
    app.state.auth_cache = InMemoryCache[Auth]()
    await broker.startup()
    try:
        # Mounted Starlette apps do not run their own lifespan; enter the session manager here.
        async with mcp.session_manager.run():
            yield
    finally:
        await link_preview_fetcher.close()
        await broker.shutdown()
        await search_index.close()
        await text_embedder.close()
        await iam_client.close()
        await engine.dispose()
