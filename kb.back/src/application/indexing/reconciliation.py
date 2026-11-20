from typing import Literal

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

from .commands import IndexArticle, ReconcileIndex
from .types import EnqueueIndexCommand

type ReconciliationMode = Literal["stale", "full"]


@dataclass(frozen=True, slots=True)
class ReconciliationQuery:
    organization_id: UUID
    generation: str
    mode: ReconciliationMode

    limit: int = 100
    after_id: UUID | None = None


type FindReconciliationCandidates = Callable[[ReconciliationQuery], Awaitable[tuple[UUID, ...]]]


async def reconcile_index(
    command: ReconcileIndex,
    *,
    find_candidates: FindReconciliationCandidates,
    enqueue: EnqueueIndexCommand,
    batch_size: int = 100,
) -> int:
    """Пакетно ставит кандидатов на индексацию.

    **Примечание**:

    Это минимальный worker, а не полноценный механизм durable orchestration.
    Для больших объёмов следует сохранять прогресс обхода либо распределять reconciliation
    по отдельным пакетным командам.
    Важно также обеспечить идемпотентность enqueue и стабильную сортировку по UUID.
    """

    cursor = None
    queued = 0

    while True:
        article_ids = await find_candidates(
            ReconciliationQuery(
                organization_id=command.organization_id,
                generation=command.generation,
                mode=command.mode,
                limit=batch_size,
                after_id=cursor,
            )
        )

        for article_id in article_ids:
            await enqueue(IndexArticle(organization_id=command.organization_id, article_id=article_id))
            queued += 1

        if len(article_ids) < batch_size:
            return queued

        cursor = article_ids[-1]
