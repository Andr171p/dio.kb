from uuid import UUID

from taskiq import TaskiqDepends, TaskiqState

from src.application.knowledge_gaps import usecases as gaps
from src.infra.broker.broker import broker


@broker.task(task_name="gaps.detect_organization", retry_on_error=True)
async def detect_gaps_task(
    organization_id: UUID,
    state: TaskiqState = TaskiqDepends(),  # noqa: B008
) -> list[str]:
    gap_ids = await gaps.run_detection(
        organization_id,
        signal_store=state.gap_signal_store,
        gap_store=state.knowledge_gap_store,
        config=state.gaps_config,
    )
    return [str(gap_id) for gap_id in gap_ids]
