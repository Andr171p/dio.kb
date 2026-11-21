from typing import Annotated

from collections.abc import AsyncIterator

from ddf.application.outbox import OutboxStore
from ddf.infra.database.sqlalchemy import PostgresConfig
from ddf.infra.outbox.sqlalchemy import SqlAlchemyOutboxStore
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database.connection import create_database
from src.infra.outbox import OUTBOX_CHANNEL

pg_config = PostgresConfig()
engine, sessionmaker = create_database(pg_config)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as session:
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db)]
UnitOfWorkDep = DBSession


def get_outbox(session: DBSession) -> OutboxStore:
    return SqlAlchemyOutboxStore(session, notify_channel=OUTBOX_CHANNEL)


OutboxDep = Annotated[OutboxStore, Depends(get_outbox)]

__all__ = ["DBSession", "OutboxDep", "engine", "sessionmaker"]
