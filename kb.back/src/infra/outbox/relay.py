"""
Outbox relay: доставляет события из ``outbox_messages`` в очередь (at-least-once).

Запуск: ``python -m src.infra.outbox.relay``. Несколько экземпляров безопасны (``FOR UPDATE SKIP LOCKED``).
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from ddf.application.outbox import OutboxConfig, OutboxProcessor
from ddf.domain.events import Event
from ddf.infra.database.sqlalchemy import PostgresConfig
from ddf.infra.outbox.sqlalchemy import PostgresOutboxListener, SqlAlchemyOutboxStore, run_postgres_notify_worker
from ddf.infra.outbox.worker import OutboxWorkerConfig

from src.application.answers.events import GenerateAnswerRequested
from src.application.indexing.commands import IndexArticle
from src.domain.articles.events import ArticleArchived, ArticlePublished, ArticleUnpublished
from src.infra.broker.broker import broker
from src.infra.broker.enqueue import enqueue_generate_answer, enqueue_index_command
from src.infra.database.connection import create_database
from src.infra.outbox import OUTBOX_CHANNEL

logger = logging.getLogger(__name__)


async def run_outbox_relay() -> None:
    pg_config = PostgresConfig()
    engine, sessionmaker = create_database(pg_config)

    async def publish(events: Sequence[Event]) -> None:
        for event in events:
            if isinstance(event, ArticlePublished | ArticleUnpublished | ArticleArchived):
                command = IndexArticle(organization_id=event.organization_id, article_id=event.article_id)
                await enqueue_index_command(command)
            elif isinstance(event, GenerateAnswerRequested):
                await enqueue_generate_answer(event.run_id)

    @asynccontextmanager
    async def processor_factory() -> AsyncIterator[OutboxProcessor]:
        async with sessionmaker() as session:
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
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_outbox_relay())
