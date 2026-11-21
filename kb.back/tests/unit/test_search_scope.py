from uuid import uuid4

from src.application.search.access import SearchScope
from src.domain.access.vo import Resource
from src.infra.qdrant.search_index import _scope_filter


def test_scope_filter_contains_tenant_and_allowed_resources() -> None:
    organization, space, article = uuid4(), uuid4(), uuid4()
    scope = SearchScope(
        organization_id=organization,
        resources=frozenset({Resource(type="space", id=space), Resource(type="article", id=article)}),
    )
    result = _scope_filter(scope, [space]).model_dump(exclude_none=True)
    assert result["must"][0]["match"]["value"] == str(organization)
    assert result["must"][1]["match"]["any"] == [str(space)]
    allowed = result["must"][2]["should"]
    assert {item["key"]: item["match"]["any"] for item in allowed} == {
        "space_id": [str(space)],
        "article_id": [str(article)],
    }
