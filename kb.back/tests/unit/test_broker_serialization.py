from typing import get_type_hints

import inspect
from uuid import uuid4

from taskiq.message import TaskiqMessage
from taskiq.receiver.params_parser import parse_params

from src.application.indexing.commands import ReconcileIndex
from src.infra.broker.broker import broker
from src.infra.broker.tasks.index_article import index_article_task
from src.infra.broker.tasks.reconcile_index import reconcile_index_task


def test_taskiq_serializes_and_restores_uuid_and_command() -> None:
    organization_id, article_id = uuid4(), uuid4()
    command = ReconcileIndex(organization_id=organization_id, generation="g1", mode="rebuild")
    for task, args in (
        (index_article_task, [organization_id, article_id, True]),
        (reconcile_index_task, [command]),
    ):
        message = TaskiqMessage(task_id=str(uuid4()), task_name=task.task_name, labels={}, args=args, kwargs={})
        encoded = broker.formatter.dumps(message)
        decoded = broker.formatter.loads(encoded.message)
        parse_params(inspect.signature(task.original_func), get_type_hints(task.original_func), decoded)
        assert decoded.args == args
        assert all(type(actual) is type(expected) for actual, expected in zip(decoded.args, args, strict=True))
