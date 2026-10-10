from ddf.application.exceptions import NotFoundError
from ddf.application.uow import UnitOfWork

from src.application.auth import AuthUser
from src.domain.access.models import AccessGrant
from src.domain.access.vo import Resource, Subject

from .dtos import AccessGrantResponse, CreateAccessGrantDTO
from .repositories import AccessGrantRepository


async def grant_access(
    dto: CreateAccessGrantDTO,
    auth: AuthUser,
    *,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> AccessGrantResponse:
    """Выдаёт права на ресурс организации; повторная выдача той же пары ресурс/субъект — 409."""

    organization_id = auth.user.organization_id
    resource = Resource(type=dto.resource.type, id=dto.resource.id)

    if not await grant_repository.resource_exists(organization_id, resource):
        raise NotFoundError(f"Resource {resource.type} with ID {resource.id} not found.")

    grant = AccessGrant(
        organization_id=organization_id,
        granted_by=auth.user.id,
        resource=resource,
        subject=Subject(type=dto.subject.type, id=dto.subject.id),
        permissions=dto.permissions,
    )
    await grant_repository.create(grant)
    await uow.commit()

    return AccessGrantResponse.model_validate(grant)


async def list_resource_grants(
    resource: Resource,
    auth: AuthUser,
    *,
    grant_repository: AccessGrantRepository,
) -> list[AccessGrantResponse]:
    grants = await grant_repository.find_by_resource(auth.user.organization_id, resource)
    return [AccessGrantResponse.model_validate(grant) for grant in grants]
