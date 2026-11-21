"""Composition root Taskiq worker."""

from contextlib import AsyncExitStack
from functools import partial

from ddf.infra.database.sqlalchemy import PostgresConfig
from taskiq import TaskiqEvents, TaskiqState

from src.infra.broker import tasks  # noqa: F401 -- регистрирует задачи на брокере
from src.infra.broker.broker import broker
from src.infra.database.connection import create_database
from src.infra.database.indexing import SqlAlchemyIndexCheckpointStore, find_candidates, load_publication, lock_article
from src.infra.qdrant import QdrantConfig, QdrantSearchIndex

from .dependencies import create_article_preparation, image_analyzer, media_client, text_embedder


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    stack = AsyncExitStack()

    try:
        pg_config = PostgresConfig()
        engine, sessionmaker = create_database(pg_config)

        qdrant_config = QdrantConfig()
        search_index = qdrant_search_index = QdrantSearchIndex(qdrant_config)

        stack.push_async_callback(text_embedder.close)
        stack.push_async_callback(image_analyzer.close)
        stack.push_async_callback(media_client.close)
        stack.push_async_callback(search_index.close)

        await qdrant_search_index.ensure_collection(text_embedder.dimensions)

        state.prepare = create_article_preparation(sessionmaker)

        state.load_publication = partial(load_publication, sessionmaker=sessionmaker)
        state.lock_article = partial(lock_article, engine=engine)
        state.find_candidates = partial(find_candidates, sessionmaker=sessionmaker)

        state.checkpoint_store = SqlAlchemyIndexCheckpointStore(sessionmaker)
        state.search_index = search_index
    except BaseException:
        await stack.aclose()
        raise

    state.resource_stack = stack


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    if (stack := getattr(state, "resource_stack", None)) is not None:
        state.resource_stack = None
        await stack.aclose()
