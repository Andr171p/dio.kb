from typing import Protocol

from uuid import UUID

from .dtos import AnswerFeedbackRequest, AnswerFeedbackResponse, AnswerResponse
from .models import AnswerRun, AnswerStage, AnswerUsage


class AnswerRunStore(Protocol):
    async def create(self, run: AnswerRun, *, session: object | None = None) -> None: ...

    async def get_by_idempotency(
        self,
        *,
        organization_id: UUID,
        principal_id: UUID,
        idempotency_key: str,
    ) -> AnswerRun | None: ...

    async def claim(self, run_id: UUID, *, owner: str, lease_seconds: int) -> AnswerRun | None: ...

    async def update_stage(
        self,
        run_id: UUID,
        stage: AnswerStage,
        *,
        metrics: dict[str, int],
        owner: str,
    ) -> int: ...

    async def complete(
        self,
        run_id: UUID,
        *,
        response: AnswerResponse,
        usage: AnswerUsage | None,
        metadata: dict[str, object],
        owner: str,
    ) -> None: ...

    async def fail(self, run_id: UUID, *, code: str, owner: str | None = None) -> None: ...

    async def get(self, run_id: UUID, *, organization_id: UUID) -> AnswerRun | None: ...


class AnswerFeedbackStore(Protocol):
    async def create_or_update(
        self,
        *,
        answer_id: UUID,
        organization_id: UUID,
        actor_id: UUID,
        request: AnswerFeedbackRequest,
    ) -> AnswerFeedbackResponse: ...
