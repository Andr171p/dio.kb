"""Composition root Taskiq worker."""

from contextlib import AsyncExitStack
from functools import partial
from uuid import uuid4

from ddf.infra.database.sqlalchemy import PostgresConfig
from redis.asyncio import Redis
from taskiq import TaskiqEvents, TaskiqState

from src.application.answers.config import AnswersConfig
from src.application.search import usecases as search_usecases
from src.infra.aitunnel import AiTunnelAnswerGenerator, AiTunnelConfig
from src.infra.broker import tasks  # noqa: F401 -- регистрирует tasks на брокере
from src.infra.broker.broker import broker
from src.infra.database.connection import create_database
from src.infra.database.indexing import SqlAlchemyIndexCheckpointStore, find_candidates, load_publication, lock_article
from src.infra.database.repositories import (
    SqlAlchemyAccessGrantRepository,
    SqlAlchemyAnswerRunStore,
    SqlAlchemyArticleQueryRepository,
)
from src.infra.qdrant import QdrantConfig, QdrantSearchIndex
from src.infra.realtime import create_answer_progress_notifier
from src.infra.redis import RedisConfig

from .dependencies import create_article_preparation, image_analyzer, media_client, text_embedder

aitunnel_config = AiTunnelConfig()  # type: ignore[call-arg]


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    stack = AsyncExitStack()

    try:
        pg_config = PostgresConfig()
        engine, sessionmaker = create_database(pg_config)

        qdrant_config = QdrantConfig()
        search_index = qdrant_search_index = QdrantSearchIndex(qdrant_config)

        answers_config = AnswersConfig()
        answer_generator = AiTunnelAnswerGenerator(
            aitunnel_config,
            max_output_tokens=answers_config.max_output_tokens,
        )

        redis_config = RedisConfig()
        redis = Redis.from_url(redis_config.url, decode_responses=True)
        progress = create_answer_progress_notifier(
            answers_config.progress_backend,
            redis_factory=lambda: redis,
        )

        stack.push_async_callback(text_embedder.close)
        stack.push_async_callback(image_analyzer.close)
        stack.push_async_callback(media_client.close)
        stack.push_async_callback(search_index.close)
        stack.push_async_callback(answer_generator.close)
        stack.push_async_callback(redis.aclose)

        await qdrant_search_index.ensure_collection(text_embedder.dimensions)

        state.prepare = create_article_preparation(sessionmaker)

        state.load_publication = partial(load_publication, sessionmaker=sessionmaker)
        state.lock_article = partial(lock_article, engine=engine)
        state.find_candidates = partial(find_candidates, sessionmaker=sessionmaker)

        state.checkpoint_store = SqlAlchemyIndexCheckpointStore(sessionmaker)
        state.search_index = search_index

        state.worker_id = str(uuid4())
        state.answers_config = answers_config
        state.answer_run_store = SqlAlchemyAnswerRunStore(sessionmaker)
        state.article_query_repository = _SessionArticleQueryRepository(sessionmaker)
        state.answer_generate = answer_generator.generate
        state.answer_progress_notify = progress.notify

        async def answer_search(organization_id, auth, dto):
            async with sessionmaker() as session:
                return await search_usecases.search_articles(
                    organization_id,
                    auth,
                    dto,
                    grant_repository=SqlAlchemyAccessGrantRepository(session),
                    article_query_repository=SqlAlchemyArticleQueryRepository(session),
                    search_index=search_index,
                    embedder=text_embedder.embed_query,
                )

        state.answer_search = answer_search
    except BaseException:
        await stack.aclose()
        raise

    state.resource_stack = stack


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    if (stack := getattr(state, "resource_stack", None)) is not None:
        state.resource_stack = None
        await stack.aclose()


class _SessionArticleQueryRepository:
    def __init__(self, sessionmaker) -> None:
        self._sessionmaker = sessionmaker

    async def find_readable_published(self, organization_id, article_ids, *, subjects, space_ids=None):
        async with self._sessionmaker() as session:
            repo = SqlAlchemyArticleQueryRepository(session)
            return await repo.find_readable_published(
                organization_id,
                article_ids,
                subjects=subjects,
                space_ids=space_ids,
            )
