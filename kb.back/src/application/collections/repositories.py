from collections.abc import Collection as Iterable
from uuid import UUID

from ddf.application.repositories import Repository

from src.domain.collections.models import Collection, CollectionPlacement
from src.domain.collections.vo import CollectionTarget


class CollectionRepository(Repository[Collection]):
    async def find_by_space(self, space_id: UUID) -> tuple[Collection, ...]:
        """Активные коллекции пространства."""


class CollectionPlacementRepository(Repository[CollectionPlacement]):
    async def lock_space_tree(self, space_id: UUID) -> None:
        """Сериализует изменения дерева коллекций Space до конца транзакции."""

    async def find_by_collection(self, collection_id: UUID) -> tuple[CollectionPlacement, ...]:
        """Элементы коллекции, отсортированные по ``rank``."""

    async def find_by_collections(self, collection_ids: Iterable[UUID]) -> tuple[CollectionPlacement, ...]: ...

    async def find_target(self, collection_id: UUID, target: CollectionTarget) -> CollectionPlacement | None: ...

    async def find_collection_parent(self, collection_id: UUID) -> CollectionPlacement | None: ...

    async def find_collection_ancestor_ids(self, collection_id: UUID) -> tuple[UUID, ...]:
        """Идентификаторы всех предков коллекции (от родителя к корню)."""

    async def find_rank_bounds(
        self,
        collection_id: UUID,
        *,
        before_id: UUID | None = None,
        after_id: UUID | None = None,
        exclude_placement_id: UUID | None = None,
    ) -> tuple[str | None, str | None]:
        """Возвращает (``before_rank``, ``after_rank``) для вставки по якорю, делая максимум 2 точечных запроса."""


__all__ = ["CollectionPlacementRepository", "CollectionRepository"]
