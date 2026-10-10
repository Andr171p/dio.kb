from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SearchChunk:
    """Фрагмент опубликованной редакции в поисковой проекции."""

    id: UUID

    organization_id: UUID
    space_id: UUID
    article_id: UUID
    revision_id: UUID

    position: int
    heading_path: tuple[str, ...]
    anchor: str | None

    text: str
    """Отображаемый фрагмент Markdown."""
    search_text: str
    """Текст для эмбеддинга и BM25: заголовки, фрагмент и распознанное содержимое изображений."""
    content_hash: str
    media_ids: tuple[UUID, ...] = ()

    dense_vector: tuple[float, ...] = ()


@dataclass(frozen=True, slots=True)
class SearchScope:
    """Разрешённая пользователю область поиска (вычисляется по READ grants до запроса в индекс)."""

    space_ids: frozenset[UUID]
    article_ids: frozenset[UUID]
    restrict_space_ids: frozenset[UUID] | None = None
    """Дополнительное сужение по выбранным пользователем пространствам."""

    @property
    def is_empty(self) -> bool:
        return not self.space_ids and not self.article_ids

    def allows(self, article_id: UUID, space_id: UUID) -> bool:
        if self.restrict_space_ids is not None and space_id not in self.restrict_space_ids:
            return False

        return space_id in self.space_ids or article_id in self.article_ids


@dataclass(frozen=True, slots=True)
class ChunkHit:
    chunk_id: UUID
    article_id: UUID
    revision_id: UUID
    score: float
    text: str
    heading_path: tuple[str, ...]
    anchor: str | None


@dataclass(frozen=True, slots=True)
class ArticleHits:
    """Лучшие фрагменты одной статьи-кандидата."""

    article_id: UUID
    score: float
    hits: tuple[ChunkHit, ...]


@dataclass(frozen=True, slots=True)
class ImageText:
    """Результат распознавания изображения: текст (OCR) и краткое описание."""

    text: str
    description: str


@dataclass(frozen=True, slots=True)
class MediaFile:
    content: bytes
    content_type: str


@dataclass(frozen=True, slots=True)
class ArticleIndexState:
    """Что из статьи сейчас лежит в индексе: используется для reconciliation."""

    article_id: UUID
    revision_id: UUID | None
    index_name: str
    chunk_count: int
    indexed_at: datetime
    failed_media_ids: tuple[UUID, ...] = ()
