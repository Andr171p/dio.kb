from ddf.infra.database.sqlalchemy import SqlAlchemyRepository

from src.domain.spaces.models import Space

from ..models import SpaceOrm


class SpaceMapper:
    def to_model(self, entity: Space) -> SpaceOrm:
        return SpaceOrm(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
            organization_id=entity.organization_id,
            key=entity.key,
            name=entity.name,
            description=entity.description,
            created_by=entity.created_by,
        )

    def from_model(self, model: SpaceOrm) -> Space:
        return Space(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            organization_id=model.organization_id,
            key=model.key,
            name=model.name,
            description=model.description,
            created_by=model.created_by,
        )


class SqlAlchemySpaceRepository(SqlAlchemyRepository[Space, SpaceOrm]):
    model = SpaceOrm
    data_mapper = SpaceMapper()
