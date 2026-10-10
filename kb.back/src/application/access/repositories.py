from collections.abc import Collection
from uuid import UUID

from ddf.application.repositories import Repository

from src.domain.access.models import AccessGrant
from src.domain.access.types import Permission
from src.domain.access.vo import Resource, Subject


class AccessGrantRepository(Repository[AccessGrant]):
    async def resolve_permission(
        self,
        organization_id: UUID,
        resources: Collection[Resource],
        subjects: Collection[Subject],
    ) -> Permission:
        """Объединяет (OR) разрешения активных grants субъектов на ресурсы."""

    async def find_resource_ids(
        self,
        organization_id: UUID,
        subjects: Collection[Subject],
        resource_type: str,
        required: Permission,
    ) -> tuple[UUID, ...]:
        """Возвращает ресурсы типа ``resource_type``, на которые у субъектов есть ``required``."""

    async def find_by_resource(
        self, organization_id: UUID, resource: Resource
    ) -> tuple[AccessGrant, ...]: ...

    async def resource_exists(self, organization_id: UUID, resource: Resource) -> bool:
        """Существует ли активный ресурс в организации (без загрузки моделей других модулей)."""


__all__ = ["AccessGrantRepository"]
