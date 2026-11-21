from collections.abc import Collection, Mapping

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infra.database.models import EmbeddingOrm


class SqlAlchemyEmbeddingCache:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def get_many(self, content_hashes: Collection[str], version: str) -> dict[str, tuple[float, ...]]:
        stmt = (
            select(EmbeddingOrm)
            .where(
                EmbeddingOrm.content_hash.in_(content_hashes),
                EmbeddingOrm.version == version,
            )
        )

        async with self._sessionmaker() as session:
            rows = await session.scalars(stmt)
            return {row.content_hash: tuple(row.vector) for row in rows}

    async def put_many(self, embeddings: Mapping[str, tuple[float, ...]], version: str) -> None:
        if embeddings:
            stmt = (
                insert(EmbeddingOrm)
                .values(
                    [
                        {
                            "content_hash": key,
                            "version": version,
                            "vector": list(vector),
                        }
                        for key, vector in embeddings.items()
                    ]
                )
                .on_conflict_do_nothing()
            )

            async with self._sessionmaker() as session, session.begin():
                await session.execute(stmt)


__all__ = ["SqlAlchemyEmbeddingCache"]
