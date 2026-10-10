"""
Задачи индексации и composition root воркера.

Запуск: ``taskiq worker src.infra.broker.tasks:broker``.
Зависимости собираются при старте воркера, а не через FastAPI ``Depends``.
"""

import logging
from dataclasses import dataclass
from uuid import UUID

from ddf.infra.database.sqlalchemy import PostgresConfig
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from taskiq import TaskiqDepends, TaskiqEvents, TaskiqState

from src.application.search.indexing import sync_article_index
from src.infra.ai import AiTunnelConfig, OpenAIImageTextExtractor, OpenAITextEmbedder, create_openai_client
from src.infra.database.repositories import (
    SqlAlchemyArticleIndexStateRepository,
    SqlAlchemyArticleRepository,
    SqlAlchemyArticleRevisionRepository,
    SqlAlchemyImageTextRepository,
)
from src.infra.database.session import create_engine, create_session_factory
from src.infra.qdrant import QdrantConfig, QdrantSearchChunkRepository, create_qdrant_client
from src.infra.services.media import SrvMediaClient, SrvMediaConfig

from .app import broker

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WorkerResources:
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    qdrant_client: AsyncQdrantClient
    chunk_repository: QdrantSearchChunkRepository
    openai_client: AsyncOpenAI
    embedder: OpenAITextEmbedder
    image_extractor: OpenAIImageTextExtractor
    media_client: SrvMediaClient


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    logging.basicConfig(level=logging.INFO)

    ai_config = AiTunnelConfig()  # type: ignore[call-arg]
    openai_client = create_openai_client(ai_config)
    embedder = OpenAITextEmbedder(
        openai_client,
        model=ai_config.embedding_model,
        dimensions=ai_config.embedding_dimensions,
        batch_size=ai_config.embedding_batch_size,
    )

    qdrant_client = create_qdrant_client(QdrantConfig())
    chunk_repository = QdrantSearchChunkRepository(qdrant_client, QdrantConfig())
    await chunk_repository.ensure_collection(embedder.dimensions)

    engine = create_engine(PostgresConfig())
    state.resources = WorkerResources(
        engine=engine,
        session_factory=create_session_factory(engine),
        qdrant_client=qdrant_client,
        chunk_repository=chunk_repository,
        openai_client=openai_client,
        embedder=embedder,
        image_extractor=OpenAIImageTextExtractor(openai_client, model=ai_config.vision_model),
        media_client=SrvMediaClient(SrvMediaConfig()),  # type: ignore[call-arg]
    )


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    resources: WorkerResources = state.resources
    await resources.media_client.close()
    await resources.openai_client.close()
    await resources.qdrant_client.close()
    await resources.engine.dispose()


@broker.task(task_name="search.sync_article_index", retry_on_error=True)
async def sync_article_index_task(article_id: str, state: TaskiqState = TaskiqDepends()) -> None:  # noqa: B008
    resources: WorkerResources = state.resources

    async with resources.session_factory() as session:
        await sync_article_index(
            UUID(article_id),
            article_repository=SqlAlchemyArticleRepository(session),
            revision_repository=SqlAlchemyArticleRevisionRepository(session),
            chunk_repository=resources.chunk_repository,
            index_state_repository=SqlAlchemyArticleIndexStateRepository(session),
            image_text_repository=SqlAlchemyImageTextRepository(session),
            media_storage=resources.media_client,
            image_extractor=resources.image_extractor,
            embedder=resources.embedder,
            uow=session,
        )


class TaskiqIndexingQueue:
    """Реализация ``IndexingQueue``: задача идемпотентна, поэтому дубли безопасны."""

    async def enqueue_article(self, article_id: UUID) -> None:
        await sync_article_index_task.kiq(str(article_id))


__all__ = ["TaskiqIndexingQueue", "broker", "sync_article_index_task"]
