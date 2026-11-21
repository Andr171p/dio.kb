from collections.abc import Collection, Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.indexing.image_analysis import ImageAnalysis
from src.infra.database.models import ImageAnalysisOrm


class SqlAlchemyImageAnalysisCache:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def get_many(self, media_ids: Collection[UUID], version: str) -> dict[UUID, ImageAnalysis]:
        if not media_ids:
            return {}

        stmt = (
            select(ImageAnalysisOrm.media_id, ImageAnalysisOrm.text, ImageAnalysisOrm.description)
            .where(ImageAnalysisOrm.media_id.in_(media_ids), ImageAnalysisOrm.version == version)
        )

        async with self._sessionmaker() as session:
            rows = (await session.execute(stmt)).all()

        return {media_id: ImageAnalysis(text=text, description=description) for media_id, text, description in rows}

    async def put(self, media_id: UUID, version: str, analysis: ImageAnalysis) -> None:
        stmt = (
            insert(ImageAnalysisOrm)
            .values(media_id=media_id, version=version, text=analysis.text, description=analysis.description)
            .on_conflict_do_nothing(index_elements=["media_id", "version"])
        )

        async with self._sessionmaker.begin() as session:
            await session.execute(stmt)

    async def put_many(self, analyses: Mapping[UUID, ImageAnalysis], version: str) -> None:
        if not analyses:
            return

        values = [
            {
                "media_id": media_id,
                "version": version,
                "text": analysis.text,
                "description": analysis.description,
            }
            for media_id, analysis in analyses.items()
        ]

        stmt = (
            insert(ImageAnalysisOrm)
            .values(values)
            .on_conflict_do_nothing(index_elements=["media_id", "version"])
        )

        async with self._sessionmaker.begin() as session:
            await session.execute(stmt)


__all__ = ["SqlAlchemyImageAnalysisCache"]
