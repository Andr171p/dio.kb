from typing import ClassVar

from dataclasses import dataclass
from uuid import UUID

from ddf.domain.events import Event


@dataclass(kw_only=True, frozen=True)
class GenerateAnswerRequested(Event):
    """Application outbox-событие: выполнить AnswerRun в worker."""

    event_type: ClassVar[str] = "answer.generate_requested"

    organization_id: UUID
    run_id: UUID
