from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Query, status

from src.api.dependencies.access import GrantRepositoryDep
from src.api.dependencies.auth import CurrentUser
from src.api.dependencies.knowledge_gaps import GapsConfigDep, GapSignalStoreDep, KnowledgeGapStoreDep
from src.application.auth.exceptions import PermissionDeniedError
from src.application.knowledge_gaps import usecases as gaps
from src.application.knowledge_gaps.dtos import (
    DismissKnowledgeGapRequest,
    KnowledgeGapListResponse,
    KnowledgeGapResponse,
    PatchKnowledgeGapRequest,
    ResolveKnowledgeGapRequest,
)
from src.domain.knowledge_gaps.types import GapStatus

router = APIRouter(prefix="/knowledge-gaps", tags=["Knowledge Gaps"])


@router.get("", summary="Список knowledge gaps")
async def list_gaps(
    auth: CurrentUser,
    gap_store: KnowledgeGapStoreDep,
    grant_repository: GrantRepositoryDep,
    status_filter: Annotated[GapStatus | None, Query(alias="status")] = None,
    space_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> KnowledgeGapListResponse:
    return await gaps.list_knowledge_gaps(
        auth,
        gap_store=gap_store,
        grant_repository=grant_repository,
        status=status_filter,
        space_id=space_id,
        limit=limit,
    )


@router.post(
    "/detect",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Запустить batch detection для организации",
)
async def detect_gaps(
    auth: CurrentUser,
    signal_store: GapSignalStoreDep,
    gap_store: KnowledgeGapStoreDep,
    config: GapsConfigDep,
) -> dict[str, object]:
    """MVP: синхронный batch в request (для пилота)."""

    if not auth.is_admin:
        raise PermissionDeniedError("Only admin can run gap detection")

    gap_ids = await gaps.run_detection(
        auth.user.organization_id,
        signal_store=signal_store,
        gap_store=gap_store,
        config=config,
    )
    return {"createdOrUpdated": [str(gap_id) for gap_id in gap_ids]}


@router.get("/{gap_id}", summary="Карточка knowledge gap")
async def get_gap(
    gap_id: UUID,
    auth: CurrentUser,
    gap_store: KnowledgeGapStoreDep,
    grant_repository: GrantRepositoryDep,
) -> KnowledgeGapResponse:
    return await gaps.get_knowledge_gap(
        auth,
        gap_id,
        gap_store=gap_store,
        grant_repository=grant_repository,
    )


@router.patch("/{gap_id}", summary="Triage / assign")
async def patch_gap(
    gap_id: UUID,
    dto: PatchKnowledgeGapRequest,
    auth: CurrentUser,
    gap_store: KnowledgeGapStoreDep,
    grant_repository: GrantRepositoryDep,
) -> KnowledgeGapResponse:
    return await gaps.patch_knowledge_gap(
        auth,
        gap_id,
        dto,
        gap_store=gap_store,
        grant_repository=grant_repository,
    )


@router.post("/{gap_id}/start", summary="Взять в работу")
async def start_gap(
    gap_id: UUID,
    auth: CurrentUser,
    gap_store: KnowledgeGapStoreDep,
    grant_repository: GrantRepositoryDep,
) -> KnowledgeGapResponse:
    return await gaps.start_knowledge_gap(
        auth,
        gap_id,
        gap_store=gap_store,
        grant_repository=grant_repository,
    )


@router.post("/{gap_id}/resolve", summary="Закрыть как выполненное")
async def resolve_gap(
    gap_id: UUID,
    dto: ResolveKnowledgeGapRequest,
    auth: CurrentUser,
    gap_store: KnowledgeGapStoreDep,
    grant_repository: GrantRepositoryDep,
) -> KnowledgeGapResponse:
    return await gaps.resolve_knowledge_gap(
        auth,
        gap_id,
        dto,
        gap_store=gap_store,
        grant_repository=grant_repository,
    )


@router.post("/{gap_id}/dismiss", summary="Отклонить")
async def dismiss_gap(
    gap_id: UUID,
    dto: DismissKnowledgeGapRequest,
    auth: CurrentUser,
    gap_store: KnowledgeGapStoreDep,
    grant_repository: GrantRepositoryDep,
) -> KnowledgeGapResponse:
    return await gaps.dismiss_knowledge_gap(
        auth,
        gap_id,
        dto,
        gap_store=gap_store,
        grant_repository=grant_repository,
    )


@router.post("/{gap_id}/reopen", summary="Открыть снова")
async def reopen_gap(
    gap_id: UUID,
    auth: CurrentUser,
    gap_store: KnowledgeGapStoreDep,
    grant_repository: GrantRepositoryDep,
) -> KnowledgeGapResponse:
    return await gaps.reopen_knowledge_gap(
        auth,
        gap_id,
        gap_store=gap_store,
        grant_repository=grant_repository,
    )
