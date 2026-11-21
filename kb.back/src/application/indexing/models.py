from typing import Annotated

from dataclasses import dataclass
from uuid import UUID

from typing_extensions import Doc


@dataclass(frozen=True, slots=True)
class MediaObject:
    """Содержимое медиа-объекта, загруженное в память."""
    content: bytes
    content_type: str


@dataclass(frozen=True, slots=True, kw_only=True)
class IndexedChunk:
    """Фрагмент опубликованной редакции в поисковой проекции."""

    id: UUID

    organization_id: UUID
    space_id: UUID
    article_id: UUID
    revision_id: UUID

    position: int
    heading_path: tuple[str, ...]
    anchor: str | None

    markdown: Annotated[str, Doc("Отображаемый фрагмент Markdown")]
    search_text: Annotated[
        str,
        Doc("Текст для эмбеддинга и BM25: заголовки, фрагмент, распознанное содержимое изображений"),
    ]
    content_hash: str

    media_ids: tuple[UUID, ...] = ()
    embedding: tuple[float, ...] | None = None
