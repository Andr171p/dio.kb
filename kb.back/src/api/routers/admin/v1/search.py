from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel

from src.api.dependencies.auth import CurrentAdmin
from src.api.dependencies.search import search_index
from src.application.indexing.commands import IndexArticle, ReconcileIndex
from src.infra.broker.enqueue import enqueue_index_command

router = APIRouter(prefix="/search", tags=["Search index"])


class QueuedResponse(BaseModel):
    task_id: UUID


@router.post("/articles/{article_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_article(article_id: UUID, auth: CurrentAdmin) -> QueuedResponse:
    return QueuedResponse(
        task_id=await enqueue_index_command(
            IndexArticle(organization_id=auth.user.organization_id, article_id=article_id, force=True)
        )
    )


@router.post("/reconcile", status_code=status.HTTP_202_ACCEPTED)
async def reconcile_index(auth: CurrentAdmin, rebuild: bool = False) -> QueuedResponse:
    command = ReconcileIndex(
        organization_id=auth.user.organization_id,
        generation=search_index.generation,
        mode="rebuild" if rebuild else "stale",
    )
    return QueuedResponse(task_id=await enqueue_index_command(command))
