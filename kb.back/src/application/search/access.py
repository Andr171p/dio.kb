from dataclasses import dataclass
from uuid import UUID

from src.application.access import AccessGrantRepository, build_subjects_from_auth
from src.application.access.exceptions import AccessDeniedError
from src.application.auth import AuthUser
from src.domain.access.types import Permission
from src.domain.access.vo import Resource, Subject

PUBLIC_SUBJECT = Subject(type="public", id="*")
SEARCHABLE_RESOURCE_TYPES = frozenset({"space", "article"})


@dataclass(frozen=True, slots=True)
class SearchScope:
    """
    Предварительно разрешённая область поиска в организации.
    Это не окончательные разрешения на выдачу данных.
    """

    organization_id: UUID
    resources: frozenset[Resource]

    @property
    def is_empty(self) -> bool:
        return not self.resources


async def resolve_search_scope(
    organization_id: UUID,
    auth: AuthUser | None,
    *,
    grant_repository: AccessGrantRepository,
) -> SearchScope:
    """Получает предварительную область ``READ`` для поиска."""

    if auth is not None and auth.user.organization_id != organization_id:
        raise AccessDeniedError("Organization missmatch.")

    subjects = frozenset({PUBLIC_SUBJECT})

    if auth is not None:
        subjects |= build_subjects_from_auth(auth)

    resources = await grant_repository.find_accessible_resources(
        organization_id,
        subjects,
        Permission.READ,
        resource_types=SEARCHABLE_RESOURCE_TYPES,
    )
    return SearchScope(organization_id=organization_id, resources=resources)
