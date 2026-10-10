from dataclasses import dataclass
from uuid import UUID

from ddf.domain.models import AggregateRoot


@dataclass(kw_only=True)
class Space(AggregateRoot):
    """Область знаний организации и базовая граница доступа."""

    organization_id: UUID

    key: str
    name: str
    description: str | None = None
    created_by: UUID
