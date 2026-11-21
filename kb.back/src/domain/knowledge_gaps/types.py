from enum import StrEnum


class GapKind(StrEnum):
    NEEDS_TRIAGE = "needs_triage"
    MISSING_CONTENT = "missing_content"
    INCOMPLETE_CONTENT = "incomplete_content"
    OUTDATED_CONTENT = "outdated_content"
    CONFLICTING_CONTENT = "conflicting_content"
    DISCOVERABILITY = "discoverability"


class GapStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
