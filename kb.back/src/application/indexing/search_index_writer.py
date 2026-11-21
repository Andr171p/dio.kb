from typing import Protocol

from collections.abc import Sequence
from uuid import UUID

from .models import IndexedChunk


class SearchIndexWriter(Protocol):
    """Запись и очистка восстанавливаемой поисковой проекции."""

    @property
    def generation(self) -> str: ...

    async def sync_revision(
        self,
        *,
        organization_id: UUID,
        article_id: UUID,
        revision_id: UUID,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        """
        Синхронизирует проекцию статьи с заданной редакцией.

        Требования:
        - повторный вызов идемпотентен;
        - после успешного завершения нет лишних старых чанков;
        - при ошибке операция может быть безопасно повторена;
        - запись не затрагивает чужие организации и статьи;
        - завершение всех операций Qdrant ожидается явно.

        Не гарантирует атомарность между PostgreSQL и Qdrant.
        """

    async def delete_article(self, *, organization_id: UUID, article_id: UUID) -> None:
        """Идемпотентно очищает проекцию статьи."""
