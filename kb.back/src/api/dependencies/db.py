from typing import Annotated

from collections.abc import AsyncIterator

from ddf.application.outbox import OutboxStore
from ddf.infra.database.sqlalchemy import PostgresConfig
from ddf.infra.outbox.sqlalchemy import SqlAlchemyOutboxStore
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infra.outbox import OUTBOX_CHANNEL

config = PostgresConfig()

engine = create_async_engine(
    config.uri,
    pool_size=config.pool_resize,
    max_overflow=config.max_overflow,
    pool_timeout=config.pool_timeout,
    pool_pre_ping=True,
    echo=config.echo,
)
sessionmaker = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as session:
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db)]
UnitOfWorkDep = DBSession


def get_outbox(session: DBSession) -> OutboxStore:
    return SqlAlchemyOutboxStore(session, notify_channel=OUTBOX_CHANNEL)


OutboxDep = Annotated[OutboxStore, Depends(get_outbox)]

__all__ = ["DBSession", "OutboxDep", "engine"]
