from uuid import UUID

from src.application.access import AccessGrantRepository, Permission, Resource
from src.application.access.guards import resolve_permissions
from src.application.auth.dtos import AuthUser
from src.domain.knowledge_gaps.models import KnowledgeGap

from .exceptions import KnowledgeGapAccessDeniedError


async def ensure_gap_access(
    auth: AuthUser,
    gap: KnowledgeGap,
    *,
    grant_repository: AccessGrantRepository,
) -> None:
    """MVP: admin или WRITE на space gap; org-level (без space) — только admin."""

    if auth.is_admin:
        return

    if gap.space_id is None:
        raise KnowledgeGapAccessDeniedError("Organization-level gaps require admin")

    permissions = await resolve_permissions(
        auth,
        [Resource(type="space", id=str(gap.space_id))],
        grant_repository=grant_repository,
    )
    if Permission.WRITE not in permissions:
        raise KnowledgeGapAccessDeniedError("Knowledge gap access denied")


async def filter_readable_gaps(
    auth: AuthUser,
    gaps: list[KnowledgeGap],
    *,
    grant_repository: AccessGrantRepository,
) -> list[KnowledgeGap]:
    if auth.is_admin:
        return gaps

    readable: list[KnowledgeGap] = []
    for gap in gaps:
        if gap.space_id is None:
            continue
        permissions = await resolve_permissions(
            auth,
            [Resource(type="space", id=str(gap.space_id))],
            grant_repository=grant_repository,
        )
        if Permission.WRITE in permissions:
            readable.append(gap)
    return readable


def assert_same_org(auth: AuthUser, organization_id: UUID) -> None:
    if auth.user.organization_id != organization_id and not auth.is_admin:
        raise KnowledgeGapAccessDeniedError("Knowledge gap access denied")
