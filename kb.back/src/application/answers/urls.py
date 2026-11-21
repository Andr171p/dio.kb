from uuid import UUID

from src.application.search.dtos import SearchArticle, SearchFragment


def build_source_url(article: SearchArticle, fragment: SearchFragment, *, base_url: str = "") -> str:
    """Собирает URL источника. Формат сменный — одна точка изменения.

    Текущий контракт: ``/spaces/{space_id}/articles/{slug}#{anchor}``.
    """

    path = f"/spaces/{article.space_id}/articles/{article.slug}"
    if fragment.anchor:
        path = f"{path}#{fragment.anchor}"

    base = base_url.rstrip("/")
    return f"{base}{path}" if base else path


def build_source_url_from_ids(
    *,
    space_id: UUID,
    slug: str,
    anchor: str | None,
    base_url: str = "",
) -> str:
    path = f"/spaces/{space_id}/articles/{slug}"
    if anchor:
        path = f"{path}#{anchor}"
    base = base_url.rstrip("/")
    return f"{base}{path}" if base else path
