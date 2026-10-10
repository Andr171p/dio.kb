from typing import Protocol

from collections.abc import Sequence
from uuid import UUID

from .models import ImageText, MediaFile


class TextEmbedder(Protocol):
    @property
    def model(self) -> str: ...

    async def embed_documents(self, texts: Sequence[str]) -> list[tuple[float, ...]]: ...

    async def embed_query(self, text: str) -> tuple[float, ...]: ...


class ImageTextExtractor(Protocol):
    """OCR и краткое поисковое описание изображения за один вызов vision-модели."""

    @property
    def version(self) -> str:
        """Модель + версия промпта: ключ кеша результатов."""
        ...

    def supports(self, content_type: str) -> bool: ...

    async def extract(self, image: MediaFile) -> ImageText: ...


class MediaStorage(Protocol):
    async def download(self, media_id: UUID) -> MediaFile: ...


class IndexingQueue(Protocol):
    async def enqueue_article(self, article_id: UUID) -> None:
        """Ставит идемпотентную синхронизацию индекса статьи в очередь."""
        ...
