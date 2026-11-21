from contextlib import asynccontextmanager
from time import time
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from jwt import encode

from src.api import lifespan
from src.api.dependencies import db
from src.api.routers.mcp import dependencies, state
from src.api.routers.mcp.config import McpConfig, mcp_config
from src.application.articles.projections import PublishedArticle
from src.application.auth import Auth, AuthType
from src.application.search.models import ArticleMatch, ChunkHit
from src.domain.access.types import Permission
from src.domain.access.vo import Resource
from src.domain.articles.logic import create_article_with_first_revision, revise_article
from src.domain.spaces.models import Space
from src.main import app


_REPOSITORY_IMPL = {
    "get_grant_repository": "SqlAlchemyAccessGrantRepository",
    "get_article_repository": "SqlAlchemyArticleRepository",
    "get_revision_repository": "SqlAlchemyArticleRevisionRepository",
    "get_article_query_repository": "SqlAlchemyArticleQueryRepository",
    "get_space_repository": "SqlAlchemySpaceRepository",
}


def _mock_repository(monkeypatch, name, repository):
    def resolve(session):
        session.append(name)
        return repository

    # Resolve() binds factories at import; patch the infra class they look up at call time.
    monkeypatch.setattr(dependencies, _REPOSITORY_IMPL[name], resolve)


def _mock_knowledge(monkeypatch):
    user_id, organization_id = uuid4(), uuid4()
    user = Auth.User(id=user_id, email="user@example.com", organization_id=organization_id)
    auth = Auth(id=user_id, type=AuthType.USER, user=user)
    space = Space(organization_id=organization_id, key="help", name="Поддержка", created_by=user_id)
    article, published = create_article_with_first_revision(
        organization_id=organization_id,
        space_id=space.id,
        author_id=user_id,
        slug="vpn",
        title="VPN",
        content="Опубликованная редакция",
    )
    article.publish(published.id)
    draft = revise_article(
        article, based_on_revision_id=published.id, author_id=user_id, title="Черновик", content="Черновик"
    )
    foreign_space = Space(organization_id=uuid4(), key="foreign", name="Другая организация", created_by=user_id)

    iam_authenticate = AsyncMock(return_value=auth)
    monkeypatch.setattr(lifespan.iam_client, "authenticate", iam_authenticate)
    monkeypatch.setattr(lifespan.iam_client, "close", AsyncMock())
    monkeypatch.setattr(lifespan.link_preview_fetcher, "close", AsyncMock())
    monkeypatch.setattr(lifespan.broker, "startup", AsyncMock())
    monkeypatch.setattr(lifespan.broker, "shutdown", AsyncMock())
    monkeypatch.setattr(lifespan.search_index, "close", AsyncMock())
    monkeypatch.setattr(lifespan.text_embedder, "close", AsyncMock())
    monkeypatch.setattr(lifespan, "engine", SimpleNamespace(dispose=AsyncMock()))
    closed_sessions = []

    @asynccontextmanager
    async def open_session():
        repos = []
        try:
            yield repos
        finally:
            closed_sessions.append(repos)

    monkeypatch.setattr(db, "sessionmaker", open_session)
    monkeypatch.setattr(state.text_embedder, "embed_query", AsyncMock(return_value=[0.1]))

    grants = AsyncMock()
    grants.find_accessible_resources.return_value = frozenset({Resource(type="space", id=space.id)})
    grants.find_resource_ids.return_value = [space.id, foreign_space.id]
    grants.resolve_permission.return_value = Permission.READ
    _mock_repository(monkeypatch, "get_grant_repository", grants)

    articles = AsyncMock()
    articles.read.side_effect = lambda article_id, **_: article if article_id == article.id else None
    revisions = AsyncMock()
    revisions.read.side_effect = {published.id: published, draft.id: draft}.get
    _mock_repository(monkeypatch, "get_article_repository", articles)
    _mock_repository(monkeypatch, "get_revision_repository", revisions)

    spaces = AsyncMock()
    spaces.get_by_ids.return_value = [space, foreign_space]
    _mock_repository(monkeypatch, "get_space_repository", spaces)

    index = AsyncMock()
    index.search.return_value = [
        ArticleMatch(
            article.id,
            1.0,
            (
                ChunkHit(uuid4(), article.id, draft.id, 1.0, draft.content, ()),
                ChunkHit(uuid4(), article.id, published.id, 0.9, published.content, ()),
            ),
        )
    ]
    monkeypatch.setattr(state, "search_index", index)
    article_queries = AsyncMock()
    article_queries.find_readable_published.return_value = [
        PublishedArticle(article.id, space.id, article.slug, published.title, published.id, published.created_at)
    ]
    _mock_repository(monkeypatch, "get_article_query_repository", article_queries)

    return iam_authenticate, article, published, space, grants, closed_sessions


def test_mcp_streamable_http(monkeypatch):
    iam_authenticate, article, published, space, grants, closed_sessions = _mock_knowledge(monkeypatch)
    resource_url = str(mcp_config.resource_url)
    resource = urlsplit(resource_url)
    origin = f"{resource.scheme}://{resource.netloc}"
    signing_key = "a-test-key-used-only-by-mcp-tests"
    jwt = encode({"aud": resource_url, "exp": int(time()) + 60}, signing_key, algorithm="HS256")
    wrong_audience = encode({"aud": "https://other.example", "exp": int(time()) + 60}, signing_key, algorithm="HS256")
    expired = encode({"aud": resource_url, "exp": int(time()) - 60}, signing_key, algorithm="HS256")
    rpc_headers = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-11-25"}
    list_tools = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

    with TestClient(app, base_url=origin, headers=rpc_headers) as client:
        unauthorized = client.post("/api/mcp/", json=list_tools)
        assert unauthorized.status_code == status.HTTP_401_UNAUTHORIZED
        metadata_path = f"/.well-known/oauth-protected-resource{resource.path}"
        assert f'resource_metadata="{origin}{metadata_path}"' in unauthorized.headers["www-authenticate"]
        assert client.get(metadata_path).json()["resource"] == resource_url

        for rejected in (wrong_audience, expired):
            headers = {"Authorization": f"Bearer {rejected}"}
            assert (
                client.post("/api/mcp/", json=list_tools, headers=headers).status_code == status.HTTP_401_UNAUTHORIZED
            )
        iam_authenticate.assert_not_awaited()

        client.headers["Authorization"] = f"Bearer {jwt}"
        response = client.post("/api/mcp", json=list_tools)
        assert response.status_code == status.HTTP_200_OK
        listed_tools = response.json()["result"]["tools"]
        properties = {tool["name"]: tool["inputSchema"]["properties"] for tool in listed_tools}
        assert all(tool["description"] for tool in listed_tools)
        assert all(field["description"] for fields in properties.values() for field in fields.values())
        assert {name: set(fields) for name, fields in properties.items()} == {
            "search_knowledge": {"query", "space_ids", "limit"},
            "get_article": {"article_id"},
            "get_spaces": set(),
        }

        def call_tool(name, **arguments):
            response = client.post(
                "/api/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                },
            )
            assert response.status_code == status.HTTP_200_OK
            return response.json()["result"]

        assert call_tool("get_spaces")["structuredContent"] == {"items": [{"id": str(space.id), "name": space.name}]}
        search = call_tool("search_knowledge", query="VPN", space_ids=[str(space.id)])["structuredContent"]
        url = f"{origin}/articles/{article.id}"
        assert search == {
            "items": [
                {"article_id": str(article.id), "title": published.title, "url": url, "fragments": [published.content]}
            ]
        }
        detail = call_tool("get_article", article_id=str(article.id))["structuredContent"]
        assert detail["markdown"] == published.content
        assert detail["title"] == published.title
        assert detail["url"] == url

        grants.resolve_permission.return_value = Permission(0)
        denied = call_tool("get_article", article_id=str(article.id))
        missing = call_tool("get_article", article_id=str(uuid4()))
        assert denied["isError"] and denied == missing
        iam_authenticate.assert_awaited_once_with(jwt)
        article_repos = {"get_article_repository", "get_revision_repository", "get_grant_repository"}
        assert [set(repos) for repos in closed_sessions] == [
            {"get_space_repository", "get_grant_repository"},
            {"get_article_query_repository", "get_grant_repository"},
            article_repos,
            article_repos,
            article_repos,
        ]


def test_mcp_config_preserves_issuer_url(monkeypatch):
    monkeypatch.delenv("MCP_ISSUER_URL", raising=False)
    assert str(McpConfig().issuer_url) == "https://iam.dios.cloud"

    monkeypatch.setenv("MCP_ISSUER_URL", "https://iam.example.com")
    assert str(McpConfig().issuer_url) == "https://iam.example.com"
