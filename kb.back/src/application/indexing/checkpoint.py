from typing import Protocol

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class IndexCheckpoint:
    """Последняя подтверждённая индексация редакции статьи."""

    article_id: UUID
    revision_id: UUID
    space_id: UUID
    generation: str
    indexed_at: datetime


class IndexCheckpointStore(Protocol):
    """Хранилище подтверждённых точек индексации."""

    async def get(self, article_id: UUID, generation: str) -> IndexCheckpoint | None: ...

    async def save_if_current(self, organization_id: UUID, checkpoint: IndexCheckpoint) -> bool:
        """
        Сохраняет checkpoint, только если статья всё ещё
        опубликована с указанной редакцией и в указанном пространстве.

        Проверка и запись выполняются в одной короткой транзакции.
        """

    async def clear_if_unpublished(self, organization_id: UUID, article_id: UUID, generation: str) -> bool:
        """Удаляет checkpoint, если статья отсутствует, архивирована или снята с публикации."""
