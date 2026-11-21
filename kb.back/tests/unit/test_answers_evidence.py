from datetime import UTC, datetime
from uuid import uuid4

from src.application.answers.citations import make_insufficient_evidence_response, validate_draft
from src.application.answers.dtos import AnswerBlock, AnswerDraft, AnswerSource, AnswerStatus
from src.application.answers.evidence import build_sources
from src.application.answers.exceptions import InvalidGeneratedAnswerError
from src.application.answers.urls import build_source_url
from src.application.search.dtos import SearchArticle, SearchFragment, SearchResponse, SearchResult


def _article(**kwargs):
    base = dict(
        id=uuid4(),
        space_id=uuid4(),
        slug="howto",
        title="How to",
        revision_id=uuid4(),
        published_at=datetime.now(UTC),
    )
    base.update(kwargs)
    return SearchArticle(**base)


def test_build_sources_skips_empty_and_dedups():
    article = _article()
    chunk = uuid4()
    response = SearchResponse(
        items=[
            SearchResult(
                article=article,
                score=1.0,
                fragments=[
                    SearchFragment(chunk_id=chunk, text="  ", heading_path=[], anchor=None, score=1.0),
                    SearchFragment(chunk_id=chunk, text="body", heading_path=["A"], anchor="a", score=0.9),
                    SearchFragment(chunk_id=chunk, text="dup", heading_path=["A"], anchor="a", score=0.8),
                ],
            )
        ]
    )

    sources = build_sources(
        response,
        build_url=lambda a, f: build_source_url(a, f),
        limit=5,
        max_chars=100,
    )
    assert len(sources) == 1
    assert sources[0].id == "src_1"
    assert sources[0].excerpt == "body"
    assert sources[0].url.endswith("#a")


def test_build_sources_respects_limit():
    article = _article()
    response = SearchResponse(
        items=[
            SearchResult(
                article=article,
                score=1.0,
                fragments=[
                    SearchFragment(chunk_id=uuid4(), text=f"t{i}", heading_path=[], anchor=None, score=1.0)
                    for i in range(5)
                ],
            )
        ]
    )
    sources = build_sources(response, build_url=lambda a, f: "u", limit=2, max_chars=10)
    assert [s.id for s in sources] == ["src_1", "src_2"]


def test_validate_draft_rejects_unknown_citation():
    draft = AnswerDraft(
        status=AnswerStatus.ANSWERED,
        blocks=[AnswerBlock(markdown="hi", citations=["src_9"])],
    )
    try:
        validate_draft(draft, {"src_1"})
        raise AssertionError("expected error")
    except InvalidGeneratedAnswerError:
        pass


def test_validate_draft_requires_citations_for_answered():
    draft = AnswerDraft(status=AnswerStatus.ANSWERED, blocks=[AnswerBlock(markdown="hi", citations=[])])
    try:
        validate_draft(draft, {"src_1"})
        raise AssertionError("expected error")
    except InvalidGeneratedAnswerError:
        pass


def test_insufficient_evidence_response():
    answer_id = uuid4()
    response = make_insufficient_evidence_response(answer_id)
    assert response.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert response.sources == []


def test_source_url_format():
    article = _article(space_id=uuid4(), slug="x")
    fragment = SearchFragment(chunk_id=uuid4(), text="t", heading_path=[], anchor="sec", score=1.0)
    assert build_source_url(article, fragment) == f"/spaces/{article.space_id}/articles/x#sec"
