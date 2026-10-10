from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ddf.infra.cache import InMemoryCache
from ddf.infra.database.sqlalchemy import PostgresConfig
from fastapi import FastAPI

from src.application.auth import Auth
from src.infra.ai import AiTunnelConfig, OpenAITextEmbedder, create_openai_client
from src.infra.broker.tasks import TaskiqIndexingQueue, broker
from src.infra.database.session import create_engine, create_session_factory
from src.infra.qdrant import QdrantConfig, QdrantSearchChunkRepository, create_qdrant_client
from src.infra.services.iam import SrvIamClient, SrvIamConfig


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Composition root API: создаёт долгоживущие клиенты и закрывает их при остановке."""

    engine = create_engine(PostgresConfig())
    iam_client = SrvIamClient(SrvIamConfig())  # type: ignore[call-arg]

    ai_config = AiTunnelConfig()  # type: ignore[call-arg]
    openai_client = create_openai_client(ai_config)
    embedder = OpenAITextEmbedder(
        openai_client,
        model=ai_config.embedding_model,
        dimensions=ai_config.embedding_dimensions,
        batch_size=ai_config.embedding_batch_size,
    )

    qdrant_config = QdrantConfig()
    qdrant_client = create_qdrant_client(qdrant_config)
    chunk_repository = QdrantSearchChunkRepository(qdrant_client, qdrant_config)
    await chunk_repository.ensure_collection(embedder.dimensions)

    await broker.startup()

    app.state.session_factory = create_session_factory(engine)
    app.state.iam_client = iam_client
    app.state.auth_cache = InMemoryCache[Auth]()
    app.state.embedder = embedder
    app.state.chunk_repository = chunk_repository
    app.state.indexing_queue = TaskiqIndexingQueue()

    try:
        yield
    finally:
        await broker.shutdown()
        await qdrant_client.close()
        await openai_client.close()
        await iam_client.close()
        await engine.dispose()


__all__ = ["lifespan"]
