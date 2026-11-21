from .dtos import AnswerDraft, AnswerResponse, AnswerSource, AnswerStatus
from .exceptions import InvalidGeneratedAnswerError


def validate_draft(draft: AnswerDraft, allowed_source_ids: set[str]) -> set[str]:
    referenced = {source_id for block in draft.blocks for source_id in block.citations}
    if not referenced.issubset(allowed_source_ids):
        raise InvalidGeneratedAnswerError("LLM referenced unknown source IDs")
    if draft.status is AnswerStatus.ANSWERED:
        if not draft.blocks or not referenced:
            raise InvalidGeneratedAnswerError("Grounded answer requires citations")
        if not any(block.markdown.strip() for block in draft.blocks):
            raise InvalidGeneratedAnswerError("Empty answer")
    return referenced


def make_response(
    answer_id,
    draft: AnswerDraft,
    sources: list[AnswerSource],
    used_ids: set[str],
) -> AnswerResponse:
    used_sources = [source for source in sources if source.id in used_ids] or list(sources)
    return AnswerResponse(
        id=answer_id,
        status=draft.status,
        blocks=draft.blocks,
        sources=used_sources,
        missing_context=list(draft.missing_context),
    )


def make_insufficient_evidence_response(answer_id) -> AnswerResponse:
    return AnswerResponse(
        id=answer_id,
        status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        blocks=[],
        sources=[],
        missing_context=[],
    )
