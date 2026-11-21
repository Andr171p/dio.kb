from typing import Protocol

from uuid import UUID

from src.domain.knowledge_gaps.models import KnowledgeGap
from src.domain.knowledge_gaps.types import GapStatus

from .dtos import GapCandidate
from .signals import GapSignal


class GapSignalStore(Protocol):
    async def record(self, signal: GapSignal) -> bool:
        """Idempotent insert. Returns True if inserted, False if duplicate."""

    async def list_unprocessed(
        self,
        organization_id: UUID,
        *,
        limit: int,
    ) -> tuple[GapSignal, ...]: ...

    async def mark_processed(self, signal_ids: tuple[UUID, ...]) -> None: ...


class KnowledgeGapStore(Protocol):
    async def read(self, gap_id: UUID, *, organization_id: UUID) -> KnowledgeGap | None: ...

    async def save(self, gap: KnowledgeGap) -> None: ...

    async def list(
        self,
        organization_id: UUID,
        *,
        status: GapStatus | None = None,
        space_id: UUID | None = None,
        owner_id: UUID | None = None,
        limit: int = 50,
    ) -> tuple[KnowledgeGap, ...]: ...

    async def upsert_candidate(self, candidate: GapCandidate) -> UUID: ...

    async def link_signals(self, gap_id: UUID, signal_ids: tuple[UUID, ...]) -> None: ...

    async def signal_count(self, gap_id: UUID) -> int: ...
