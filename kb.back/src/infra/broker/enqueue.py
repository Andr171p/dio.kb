from uuid import UUID

from src.application.indexing.commands import IndexArticle, IndexCommand


async def enqueue_index_command(command: IndexCommand) -> UUID:
    from src.infra.broker.tasks import index_article_task, reconcile_index_task

    if isinstance(command, IndexArticle):
        result = await index_article_task.kiq(command.organization_id, command.article_id, command.force)
    else:
        result = await reconcile_index_task.kiq(command)

    return UUID(result.task_id)
