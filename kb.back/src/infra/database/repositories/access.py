from collections.abc import Collection
from uuid import UUID

from ddf.infra.database.sqlalchemy import SqlAlchemyRepository
from sqlalchemy import ColumnElement, exists, func, select, tuple_

from src.application.access.repositories import AccessGrantRepository
from src.domain.access.models import AccessGrant
from src.domain.access.types import Permission
from src.domain.access.vo import Resource, Subject

from ..models import AccessGrantOrm, ArticleOrm, CollectionOrm, SpaceOrm

_RESOURCE_MODELS = {"space": SpaceOrm, "collection": CollectionOrm, "article": ArticleOrm}


class AccessGrantMapper:
    def to_model(self, entity: AccessGrant) -> AccessGrantOrm:
        return AccessGrantOrm(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
            organization_id=entity.organization_id,
            granted_by=entity.granted_by,
            resource_type=entity.resource.type,
            resource_id=entity.resource.id,
            subject_type=entity.subject.type,
            subject_id=entity.subject.id,
            permissions=int(entity.permissions),
        )

    def from_model(self, model: AccessGrantOrm) -> AccessGrant:
        return AccessGrant(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            organization_id=model.organization_id,
            granted_by=model.granted_by,
            resource=Resource(type=model.resource_type, id=model.resource_id),
            subject=Subject(type=model.subject_type, id=model.subject_id),
            permissions=Permission(model.permissions),
        )


class SqlAlchemyAccessGrantRepository(
    SqlAlchemyRepository[AccessGrant, AccessGrantOrm], AccessGrantRepository
):
    model = AccessGrantOrm
    data_mapper = AccessGrantMapper()

    def _active_subject_grants(
        self,
        organization_id: UUID,
        subjects: Collection[Subject],
    ) -> tuple[ColumnElement[bool], ...]:
        return (
            AccessGrantOrm.organization_id == organization_id,
            AccessGrantOrm.deleted_at.is_(None),
            tuple_(AccessGrantOrm.subject_type, AccessGrantOrm.subject_id).in_(
                [(subject.type, subject.id) for subject in subjects],
            ),
        )

    async def resolve_permission(
        self,
        organization_id: UUID,
        resources: Collection[Resource],
        subjects: Collection[Subject],
    ) -> Permission:
        if not resources or not subjects:
            return Permission(0)

        stmt = select(func.coalesce(func.bit_or(AccessGrantOrm.permissions), 0)).where(
            *self._active_subject_grants(organization_id, subjects),
            tuple_(AccessGrantOrm.resource_type, AccessGrantOrm.resource_id).in_(
                [(resource.type, resource.id) for resource in resources],
            ),
        )
        return Permission(await self._session.scalar(stmt) or 0)

    async def find_resource_ids(
        self,
        organization_id: UUID,
        subjects: Collection[Subject],
        resource_type: str,
        required: Permission,
    ) -> tuple[UUID, ...]:
        if not subjects:
            return ()

        stmt = (
            select(AccessGrantOrm.resource_id)
            .where(
                *self._active_subject_grants(organization_id, subjects),
                AccessGrantOrm.resource_type == resource_type,
            )
            .group_by(AccessGrantOrm.resource_id)
            .having(func.bit_or(AccessGrantOrm.permissions).op("&")(int(required)) == int(required))
        )
        return tuple(await self._session.scalars(stmt))

    async def find_by_resource(self, organization_id: UUID, resource: Resource) -> tuple[AccessGrant, ...]:
        stmt = (
            select(AccessGrantOrm)
            .where(
                AccessGrantOrm.organization_id == organization_id,
                AccessGrantOrm.deleted_at.is_(None),
                AccessGrantOrm.resource_type == resource.type,
                AccessGrantOrm.resource_id == resource.id,
            )
            .order_by(AccessGrantOrm.created_at)
        )
        return tuple(self.data_mapper.from_model(model) for model in await self._session.scalars(stmt))

    async def resource_exists(self, organization_id: UUID, resource: Resource) -> bool:
        if (model := _RESOURCE_MODELS.get(resource.type)) is None:
            return False

        stmt = select(
            exists().where(
                model.id == resource.id,
                model.organization_id == organization_id,
                model.deleted_at.is_(None),
            ),
        )
        return bool(await self._session.scalar(stmt))
