from collections.abc import Collection as Iterable
from uuid import UUID

from ddf.infra.database.sqlalchemy import SqlAlchemyRepository
from sqlalchemy import ColumnElement, func, select, text

from src.application.collections.repositories import CollectionPlacementRepository, CollectionRepository
from src.domain.collections.models import Collection, CollectionPlacement
from src.domain.collections.vo import CollectionTarget, TargetType

from ..models import CollectionOrm, CollectionPlacementOrm

# Защита от зацикливания при повреждённых данных
_MAX_TREE_DEPTH = 100

_ANCESTORS_QUERY = text("""
    WITH RECURSIVE ancestors(collection_id, depth) AS (
        SELECT collection_id, 1
        FROM collection_placements
        WHERE target_type = 'collection' AND target_id = :collection_id
        UNION ALL
        SELECT placement.collection_id, ancestors.depth + 1
        FROM collection_placements AS placement
        JOIN ancestors
            ON placement.target_type = 'collection' AND placement.target_id = ancestors.collection_id
        WHERE ancestors.depth < :max_depth
    )
    SELECT collection_id FROM ancestors ORDER BY depth
""")


class CollectionMapper:
    def to_model(self, entity: Collection) -> CollectionOrm:
        return CollectionOrm(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
            organization_id=entity.organization_id,
            space_id=entity.space_id,
            name=entity.name,
            slug=entity.slug,
            description=entity.description,
        )

    def from_model(self, model: CollectionOrm) -> Collection:
        return Collection(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            organization_id=model.organization_id,
            space_id=model.space_id,
            name=model.name,
            slug=model.slug,
            description=model.description,
        )


class CollectionPlacementMapper:
    def to_model(self, entity: CollectionPlacement) -> CollectionPlacementOrm:
        return CollectionPlacementOrm(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
            collection_id=entity.collection_id,
            target_type=entity.target.type.value,
            target_id=entity.target.id,
            rank=entity.rank,
        )

    def from_model(self, model: CollectionPlacementOrm) -> CollectionPlacement:
        return CollectionPlacement(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            collection_id=model.collection_id,
            target=CollectionTarget(type=TargetType(model.target_type), id=model.target_id),
            rank=model.rank,
        )


class SqlAlchemyCollectionRepository(SqlAlchemyRepository[Collection, CollectionOrm], CollectionRepository):
    model = CollectionOrm
    data_mapper = CollectionMapper()

    async def find_by_space(self, space_id: UUID) -> tuple[Collection, ...]:
        stmt = select(CollectionOrm).where(
            CollectionOrm.space_id == space_id, CollectionOrm.deleted_at.is_(None)
        )
        return tuple(self.data_mapper.from_model(model) for model in await self._session.scalars(stmt))


class SqlAlchemyCollectionPlacementRepository(
    SqlAlchemyRepository[CollectionPlacement, CollectionPlacementOrm],
    CollectionPlacementRepository,
):
    model = CollectionPlacementOrm
    data_mapper = CollectionPlacementMapper()

    async def lock_space_tree(self, space_id: UUID) -> None:
        key = f"collection-tree:{space_id}"
        await self._session.execute(select(func.pg_advisory_xact_lock(func.hashtextextended(key, 0))))

    async def _find(self, *conditions: ColumnElement[bool]) -> tuple[CollectionPlacement, ...]:
        stmt = (
            select(CollectionPlacementOrm)
            .where(*conditions)
            .order_by(
                CollectionPlacementOrm.rank,
                CollectionPlacementOrm.id,
            )
        )
        return tuple(self.data_mapper.from_model(model) for model in await self._session.scalars(stmt))

    async def find_by_collection(self, collection_id: UUID) -> tuple[CollectionPlacement, ...]:
        return await self._find(CollectionPlacementOrm.collection_id == collection_id)

    async def find_by_collections(self, collection_ids: Iterable[UUID]) -> tuple[CollectionPlacement, ...]:
        if not collection_ids:
            return ()

        return await self._find(CollectionPlacementOrm.collection_id.in_(list(collection_ids)))

    async def find_target(self, collection_id: UUID, target: CollectionTarget) -> CollectionPlacement | None:
        placements = await self._find(
            CollectionPlacementOrm.collection_id == collection_id,
            CollectionPlacementOrm.target_type == target.type.value,
            CollectionPlacementOrm.target_id == target.id,
        )
        return placements[0] if placements else None

    async def find_collection_parent(self, collection_id: UUID) -> CollectionPlacement | None:
        placements = await self._find(
            CollectionPlacementOrm.target_type == TargetType.COLLECTION.value,
            CollectionPlacementOrm.target_id == collection_id,
        )
        return placements[0] if placements else None

    async def find_collection_ancestor_ids(self, collection_id: UUID) -> tuple[UUID, ...]:
        result = await self._session.execute(
            _ANCESTORS_QUERY,
            {"collection_id": collection_id, "max_depth": _MAX_TREE_DEPTH},
        )
        return tuple(result.scalars())
