from ddf.domain.exceptions import InvalidStateError


class KnowledgeGapInvalidStateError(InvalidStateError):
    error_code = "knowledge_gap_invalid_state"
