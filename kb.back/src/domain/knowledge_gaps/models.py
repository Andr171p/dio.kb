from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from ddf.domain.models import AggregateRoot

from .exceptions import KnowledgeGapInvalidStateError
from .types import GapKind, GapStatus


@dataclass(kw_only=True)
class KnowledgeGap(AggregateRoot):
    """Редакторская задача по устранению установленной проблемы в знаниях."""

    organization_id: UUID
    grouping_key: str
    title: str
    space_id: UUID | None = None
    kind: GapKind = GapKind.NEEDS_TRIAGE
    status: GapStatus = GapStatus.OPEN
    owner_id: UUID | None = None
    related_article_id: UUID | None = None
    resolution_note: str | None = None
    rationale: str | None = None

    def triage(self, kind: GapKind, *, article_id: UUID | None = None) -> None:
        self._ensure_open()
        if kind is GapKind.NEEDS_TRIAGE:
            raise KnowledgeGapInvalidStateError("Concrete gap kind required")
        self.kind = kind
        self.related_article_id = article_id
        self.updated_at = datetime.now(UTC)

    def assign(self, owner_id: UUID) -> None:
        self._ensure_open()
        self.owner_id = owner_id
        self.updated_at = datetime.now(UTC)

    def start(self) -> None:
        self._ensure_open()
        if self.kind is GapKind.NEEDS_TRIAGE:
            raise KnowledgeGapInvalidStateError("Triage required before start")
        self.status = GapStatus.IN_PROGRESS
        self.updated_at = datetime.now(UTC)

    def resolve(self, note: str) -> None:
        if self.status is not GapStatus.IN_PROGRESS:
            raise KnowledgeGapInvalidStateError("Gap must be in progress")
        if not note.strip():
            raise KnowledgeGapInvalidStateError("Resolution note is required")
        self.status = GapStatus.RESOLVED
        self.resolution_note = note.strip()
        self.updated_at = datetime.now(UTC)

    def dismiss(self, reason: str) -> None:
        self._ensure_open()
        if not reason.strip():
            raise KnowledgeGapInvalidStateError("Dismiss reason is required")
        self.status = GapStatus.DISMISSED
        self.resolution_note = reason.strip()
        self.updated_at = datetime.now(UTC)

    def reopen(self) -> None:
        if self.status not in (GapStatus.RESOLVED, GapStatus.DISMISSED):
            raise KnowledgeGapInvalidStateError("Only a closed gap can be reopened")
        self.status = GapStatus.OPEN
        self.resolution_note = None
        self.updated_at = datetime.now(UTC)

    def _ensure_open(self) -> None:
        if self.status in (GapStatus.RESOLVED, GapStatus.DISMISSED):
            raise KnowledgeGapInvalidStateError("Closed gap cannot be changed")
