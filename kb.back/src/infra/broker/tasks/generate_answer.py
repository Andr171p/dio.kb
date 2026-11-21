from uuid import UUID

from taskiq import TaskiqDepends, TaskiqState

from src.application.answers import usecases as answers
from src.infra.broker.broker import broker


@broker.task(task_name="answers.generate_answer", retry_on_error=True)
async def generate_answer_task(run_id: UUID, state: TaskiqState = TaskiqDepends()) -> None:  # noqa: B008
    await answers.execute_answer_run(
        run_id,
        store=state.answer_run_store,
        search=state.answer_search,
        generate=state.answer_generate,
        article_query_repository=state.article_query_repository,
        config=state.answers_config,
        notify=state.answer_progress_notify,
        owner=f"worker:{state.worker_id}",
        gap_signal_store=state.gap_signal_store,
        gaps_config=state.gaps_config,
    )
