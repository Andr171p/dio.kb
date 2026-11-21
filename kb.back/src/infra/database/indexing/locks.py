import asyncio
import hashlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine


def _lock_key(organization_id: UUID, article_id: UUID) -> int:
    """Стабильный signed bigint для PostgreSQL advisory lock."""
    digest = hashlib.blake2b(b"dios-kb:index:" + organization_id.bytes + article_id.bytes, digest_size=8).digest()
    return int.from_bytes(digest, "big", signed=True)


async def _unlock_and_cleanup(connection: AsyncConnection, key: int) -> None:
    try:
        released = await connection.scalar(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
        await connection.commit()

        if released is not True:
            raise RuntimeError("PostgreSQL advisory lock was not held")
    except BaseException:
        await connection.invalidate()
        raise


@asynccontextmanager
async def lock_article(
    organization_id: UUID,
    article_id: UUID,
    *,
    engine: AsyncEngine,
    timeout: float = 15.0,
) -> AsyncIterator[None]:
    """Сериализует запись индекса без долгой PostgreSQL-транзакции."""

    key = _lock_key(organization_id, article_id)

    async with engine.connect() as connection:
        try:
            async with asyncio.timeout(timeout):
                await connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": key})

            await connection.commit()
        except BaseException:
            await connection.invalidate()
            raise

        try:
            yield
        finally:
            await _unlock_and_cleanup(connection, key)


__all__ = ["lock_article"]
