from taskiq import TaskiqDepends, TaskiqState

from src.application.indexing.commands import ReconcileIndex
from src.application.indexing.reconciliation import reconcile_index
from src.infra.broker.broker import broker


@broker.task(task_name="indexing.reconcile_index", retry_on_error=True)
async def reconcile_index_task(command: dict, state: TaskiqState = TaskiqDepends()) -> None:  # noqa: B008
    from src.infra.broker.enqueue import enqueue_index_command

    request = ReconcileIndex.model_validate(command)
    if request.generation != state.index.generation:
        raise ValueError("Reconciliation generation does not match worker index")
    await reconcile_index(request, find_candidates=state.repository.find_candidates, enqueue=enqueue_index_command)
