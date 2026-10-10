from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Resource:
    """Ресурс к которому предоставляют доступ."""

    type: str
    id: UUID


@dataclass(frozen=True, slots=True)
class Subject:
    """Тот кому предоставляется доступ."""

    type: str
    id: str
