from typing import Protocol

from .dtos import LinkPreviewResponse


class LinkPreviewFetcher(Protocol):
    async def fetch(self, url: str) -> LinkPreviewResponse:
        """Загружает метаданные публичной страницы; внутренние адреса сети не запрашиваются."""
        ...
