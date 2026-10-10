"""
Outbox relay: доставляет события из ``outbox_messages`` в очередь индексации (at-least-once).

Запуск: ``python -m src.infra.outbox.relay``. Несколько экземпляров безопасны (``FOR UPDATE SKIP LOCKED``).
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from ddf.application.outbox import OutboxConfig, OutboxProcessor
from ddf.domain.events import Event
from ddf.infra.database.sqlalchemy import PostgresConfig
from ddf.infra.outbox.sqlalchemy import (
    PostgresOutboxListener,
    SqlAlchemyOutboxStore,
    run_postgres_notify_worker,
)
from ddf.infra.outbox.worker import OutboxWorkerConfig
from dotenv import load_dotenv

from src.domain.articles.events import ArticleArchived, ArticlePublished, ArticleUnpublished
from src.infra.broker.tasks import TaskiqIndexingQueue, broker
from src.infra.database.session import create_engine, create_session_factory
from src.infra.outbox import OUTBOX_CHANNEL

logger = logging.getLogger(__name__)


async def run_outbox_relay() -> None:
    engine = create_engine(PostgresConfig())
    session_factory = create_session_factory(engine)
    indexing_queue = TaskiqIndexingQueue()

    async def publish(events: Sequence[Event]) -> None:
        for event in events:
            if isinstance(event, ArticlePublished | ArticleUnpublished | ArticleArchived):
                await indexing_queue.enqueue_article(event.article_id)

    @asynccontextmanager
    async def processor_factory() -> AsyncIterator[OutboxProcessor]:
        async with session_factory() as session:
            yield OutboxProcessor(
                uow=session,
                outbox_store=SqlAlchemyOutboxStore(session),
                publisher=publish,
                config=OutboxConfig(),
            )

    await broker.startup()
    logger.info("Outbox relay started")

    try:
        await run_postgres_notify_worker(
            processor_factory,
            PostgresOutboxListener(engine, channel=OUTBOX_CHANNEL),
            OutboxWorkerConfig(),
        )
    finally:
        await broker.shutdown()
        await engine.dispose()


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_outbox_relay())
