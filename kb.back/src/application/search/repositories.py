from typing import Protocol

from collections.abc import Sequence
from uuid import UUID

from .models import ArticleHits, ArticleIndexState, ImageText, SearchChunk, SearchScope


class SearchChunkRepository(Protocol):
    """Поисковая проекция опубликованных редакций (восстанавливаемая, не источник истины)."""

    @property
    def index_name(self) -> str:
        """Имя физического индекса (меняется вместе с поколением модели/парсера)."""
        ...

    async def replace_article_chunks(
        self,
        article_id: UUID,
        revision_id: UUID,
        chunks: Sequence[SearchChunk],
    ) -> None:
        """Сохраняет фрагменты редакции и удаляет фрагменты прочих редакций статьи."""
        ...

    async def delete_article_chunks(self, article_id: UUID) -> None: ...

    async def find_article_vectors(self, article_id: UUID) -> dict[str, tuple[float, ...]]:
        """Сохранённые dense-векторы статьи по ``content_hash`` (для переиспользования)."""
        ...

    async def search(
        self,
        *,
        query: str,
        query_vector: Sequence[float],
        organization_id: UUID,
        scope: SearchScope,
        limit: int,
        hits_per_article: int,
    ) -> list[ArticleHits]:
        """Гибридный поиск строго внутри ``scope``, сгруппированный по статьям."""
        ...


class ImageTextRepository(Protocol):
    """Кеш распознанных изображений (медиа неизменяемы по идентификатору)."""

    async def find(self, media_ids: Sequence[UUID], version: str) -> dict[UUID, ImageText]: ...

    async def save(self, media_id: UUID, version: str, image_text: ImageText) -> None: ...


class ArticleIndexStateRepository(Protocol):
    async def lock(self, article_id: UUID) -> None:
        """Сериализует запись индекса одной статьи до конца транзакции."""
        ...

    async def save(self, state: ArticleIndexState) -> None: ...

    async def find_out_of_sync_article_ids(self, index_name: str, *, full: bool = False) -> tuple[UUID, ...]:
        """Статьи с расхождением индекса и PostgreSQL; ``full`` — все, что есть или должно быть в индексе."""
        ...


__all__ = ["ArticleIndexStateRepository", "ImageTextRepository", "SearchChunkRepository"]
