from dataclasses import dataclass
from uuid import UUID

from ddf.domain.models import AggregateRoot

from .types import Permission
from .vo import Resource, Subject


@dataclass(kw_only=True)
class AccessGrant(AggregateRoot):
    """Разрешения субъекта на ресурс."""

    organization_id: UUID
    granted_by: UUID
    resource: Resource
    subject: Subject
    permissions: Permission
