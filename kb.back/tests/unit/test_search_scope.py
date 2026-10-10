import uuid

from src.application.search.models import SearchScope


def test_scope_allows_space_or_direct_article_within_restriction() -> None:
    space, other_space, article = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    scope = SearchScope(space_ids=frozenset({space}), article_ids=frozenset({article}))

    assert scope.allows(uuid.uuid4(), space)
    assert scope.allows(article, other_space)
    assert not scope.allows(uuid.uuid4(), other_space)

    restricted = SearchScope(
        space_ids=frozenset({space}),
        article_ids=frozenset({article}),
        restrict_space_ids=frozenset({space}),
    )
    assert not restricted.allows(article, other_space)
