from taskiq import TaskiqDepends, TaskiqState

from src.application.indexing.commands import ReconcileIndex
from src.application.indexing.reconciliation import reconcile_index
from src.infra.broker.broker import broker


@broker.task(task_name="indexing.reconcile_index", retry_on_error=True)
async def reconcile_index_task(command: ReconcileIndex, state: TaskiqState = TaskiqDepends()) -> None:  # noqa: B008
    from src.infra.broker.enqueue import enqueue_index_command

    if command.generation != state.index.generation:
        raise ValueError("Reconciliation generation does not match worker index")
    await reconcile_index(command, find_candidates=state.find_candidates, enqueue=enqueue_index_command)
