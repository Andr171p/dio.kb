from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ddf.infra.cache import InMemoryCache
from fastapi import FastAPI
from mcp.server import MCPServer
from redis.asyncio import Redis

from src.api.dependencies.auth import iam_client
from src.api.dependencies.db import engine
from src.api.dependencies.links import link_preview_fetcher
from src.api.dependencies.search import search_index, text_embedder
from src.application.answers.config import AnswersConfig
from src.application.auth import Auth
from src.infra.broker.broker import broker
from src.infra.realtime import create_answer_progress_notifier
from src.infra.redis import RedisConfig


@asynccontextmanager
async def lifespan(app: FastAPI, *, mcp: MCPServer) -> AsyncIterator[None]:
    # noinspection PyUnresolvedReferences
    app.state.iam_client = iam_client
    # noinspection PyUnresolvedReferences
    app.state.auth_cache = InMemoryCache[Auth]()

    answers_config = AnswersConfig()
    redis: Redis | None = None
    if answers_config.progress_backend.value == "redis":
        redis = Redis.from_url(RedisConfig().url, decode_responses=True)
        app.state.redis = redis
        app.state.answer_progress_notifier = create_answer_progress_notifier(
            answers_config.progress_backend,
            redis_factory=lambda: redis,
        )
    else:
        app.state.redis = None
        app.state.answer_progress_notifier = create_answer_progress_notifier(answers_config.progress_backend)

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
        if redis is not None:
            await redis.aclose()
        await engine.dispose()
