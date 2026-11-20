from uuid import UUID

from taskiq import TaskiqDepends, TaskiqState

from src.application.indexing.indexing import index_article
from src.application.indexing.types import IndexOutcome
from src.infra.broker.broker import broker


@broker.task(task_name="indexing.index_article", retry_on_error=True)
async def index_article_task(
    organization_id: str,
    article_id: str,
    force: bool = False,
    state: TaskiqState = TaskiqDepends(),  # noqa: B008
) -> None:
    repository = state.repository
    outcome = await index_article(
        UUID(organization_id),
        UUID(article_id),
        load_publication=repository.load_publication,
        prepare_chunks=state.prepare,
        lock_article=repository.lock_article,
        index_writer=state.index,
        checkpoint_store=repository,
        force=force,
    )
    if outcome == IndexOutcome.SUPERSEDED:
        raise RuntimeError("Publication changed during indexing; retry required")
