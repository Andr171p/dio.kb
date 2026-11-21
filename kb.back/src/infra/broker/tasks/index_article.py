from uuid import UUID

from taskiq import TaskiqDepends, TaskiqState

from src.application.indexing.indexing import index_article
from src.application.indexing.types import IndexOutcome
from src.infra.broker.broker import broker


@broker.task(task_name="indexing.index_article", retry_on_error=True)
async def index_article_task(
    organization_id: UUID,
    article_id: UUID,
    force: bool = False,
    state: TaskiqState = TaskiqDepends(),  # noqa: B008
) -> None:
    outcome = await index_article(
        organization_id,
        article_id,
        load_publication=state.load_publication,
        prepare_chunks=state.prepare,
        lock_article=state.lock_article,
        index_writer=state.search_index,
        checkpoint_store=state.checkpoint_store,
        force=force,
    )
    if outcome == IndexOutcome.SUPERSEDED:
        raise RuntimeError("Publication changed during indexing; retry required")
