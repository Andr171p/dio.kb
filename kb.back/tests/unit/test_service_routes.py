from src.main import app


def test_service_routes_are_read_only_except_search() -> None:
    paths = app.openapi()["paths"]
    assert "200" in paths["/api/service/v1/articles/{article_id}"]["get"]["responses"]
    assert "200" in paths["/api/service/v1/collections/{collection_id}/placements"]["get"]["responses"]
    assert "200" in paths["/api/service/v1/search"]["post"]["responses"]
    assert "200" in paths["/api/service/v1/search/suggestions"]["post"]["responses"]
    for path, operations in paths.items():
        if path.startswith("/api/service/"):
            assert set(operations) <= ({"get", "post"} if path.startswith("/api/service/v1/search") else {"get"})


def test_service_routes_reject_non_service_identity() -> None:
    from uuid import uuid4

    from fastapi import status
    from fastapi.testclient import TestClient

    from src.api.dependencies.auth import get_current_auth
    from src.application.auth import Auth, AuthType

    user_id, organization_id = uuid4(), uuid4()
    auth = Auth(
        id=user_id,
        type=AuthType.USER,
        user=Auth.User(id=user_id, email="user@example.com", organization_id=organization_id, roles=frozenset()),
    )
    app.dependency_overrides[get_current_auth] = lambda: auth
    try:
        client = TestClient(app)
        assert (
            client.get("/api/service/v1/link-preview", params={"url": "https://example.com"}).status_code
            == status.HTTP_403_FORBIDDEN
        )
        assert client.post("/api/service/v1/search", json={"query": "VPN"}).status_code == status.HTTP_403_FORBIDDEN
    finally:
        app.dependency_overrides.pop(get_current_auth, None)
