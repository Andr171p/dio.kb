from collections.abc import Callable

from src.application.search.dtos import SearchArticle, SearchFragment, SearchResponse

from .dtos import AnswerSource

type BuildSourceUrl = Callable[[SearchArticle, SearchFragment], str]


def build_sources(
    search_results: SearchResponse,
    *,
    build_url: BuildSourceUrl,
    limit: int,
    max_chars: int,
) -> list[AnswerSource]:
    """Адаптер SearchResponse → AnswerSource.

    Предусловие: ``search_results`` уже прошёл актуальную ACL/publication check.
    """

    result: list[AnswerSource] = []
    seen: set[tuple[object, object, object]] = set()

    for match in search_results.items:
        article = match.article
        for fragment in match.fragments:
            key = (article.id, article.revision_id, fragment.chunk_id)
            if key in seen or not fragment.text.strip():
                continue
            seen.add(key)
            result.append(
                AnswerSource(
                    id=f"src_{len(result) + 1}",
                    article_id=article.id,
                    revision_id=article.revision_id,
                    chunk_id=fragment.chunk_id,
                    title=article.title,
                    url=build_url(article, fragment),
                    excerpt=fragment.text[:max_chars],
                    anchor=fragment.anchor,
                )
            )
            if len(result) >= limit:
                return result
    return result
