from typing import Protocol

import asyncio
import logging
from collections.abc import Awaitable, Callable, Collection, Sequence
from dataclasses import dataclass
from uuid import UUID

from .config import ImageProcessingConfig
from .models import MediaObject
from .types import OpenMedia
from .utils import read_limited

logger = logging.getLogger(__name__)

type AnalyzeImage = Callable[[UUID], Awaitable[ImageAnalysis]]


@dataclass(frozen=True, slots=True)
class ImageAnalysis:
    """Извлечённый текст и визуальное описание изображения."""
    text: str
    description: str


class ImageAnalyzer(Protocol):
    """Извлечение текста и визуального контекста изображения."""

    @property
    def version(self) -> str:
        """Версия алгоритма анализа для кеширования."""

    async def analyze(self, image: MediaObject) -> ImageAnalysis:
        """Распознаёт текст и описывает визуальное содержимое."""


class ImageAnalysisCache(Protocol):
    """Кеш результатов анализа неизменяемых изображений."""

    async def get_many(self, media_ids: Collection[UUID], version: str) -> dict[UUID, ImageAnalysis]: ...

    async def put(self, media_id: UUID, version: str, analysis: ImageAnalysis) -> None: ...


async def analyze_image(
    media_id: UUID,
    content_type: str,
    *,
    open_media: OpenMedia,
    analyzer: ImageAnalyzer,
    max_bytes: int,
) -> ImageAnalysis:
    """Читает изображение с ограничением размера и выполняет его анализ (без кеша)."""

    async with open_media(media_id) as chunks:
        content = await read_limited(chunks, max_bytes=max_bytes)

    return await analyzer.analyze(MediaObject(content=content, content_type=content_type))


async def analyze_images(
    media_ids: Sequence[UUID],
    *,
    analyze: AnalyzeImage,
    cache: ImageAnalysisCache,
    analyzer_version: str,
    config: ImageProcessingConfig,
) -> tuple[dict[UUID, ImageAnalysis], tuple[UUID, ...]]:
    """Batch-анализ с кешированием и изоляцией ошибок медиа.

    Trades-off первой версии (допустимо как fallback), но для production лучше различать:
    - ``retryable``: timeout, 429, временная недоступность;
    - ``permanent``: повреждённый файл, запрещённый или неподдерживаемый формат;
    - ``skipped``: медиа заведомо не требует vision-анализа.
    """

    ids = tuple(dict.fromkeys(media_ids))
    if not ids:
        return {}, ()

    version = config.analyzer_version or analyzer_version
    analyses = await cache.get_many(ids, version)
    missing = (media_id for media_id in ids if media_id not in analyses)

    failed: set[UUID] = set()
    semaphore = asyncio.Semaphore(config.max_concurrent_analyses)

    async def process(media_id: UUID) -> None:
        async with semaphore:
            # noinspection PyBroadException
            try:
                analysis = await analyze(media_id)
            except Exception:
                logger.exception("Image analysis failed", extra={"media_id": str(media_id)})
                failed.add(media_id)
                return

            # Ошибка кеша не считается ошибкой изображения.
            await cache.put(media_id, version, analysis)
            analyses[media_id] = analysis

    async with asyncio.TaskGroup() as group:
        for media_id in missing:
            group.create_task(process(media_id))

    return analyses, tuple(media_id for media_id in ids if media_id in failed)
