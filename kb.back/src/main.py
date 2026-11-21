"""ASGI-приложение DIOS Knowledge. Запуск: ``uvicorn src.main:app``."""

import logging
from functools import partial
from urllib.parse import urlsplit

from fastapi import FastAPI, status
from mcp.server.auth.routes import create_protected_resource_routes
from mcp.server.transport_security import TransportSecuritySettings

from src.api.exception_handlers import register_exception_handlers
from src.api.lifespan import lifespan
from src.api.routers import router
from src.api.routers.mcp import mcp
from src.api.routers.mcp.config import mcp_config

logging.basicConfig(level=logging.INFO)

resource = urlsplit(str(mcp_config.resource_url))
mcp_http_app = mcp.streamable_http_app(
    streamable_http_path="/",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[resource.netloc],
        allowed_origins=[f"{resource.scheme}://{resource.netloc}"],
    ),
)

app = FastAPI(title="DIOS Knowledge", version="0.1.0", lifespan=partial(lifespan, mcp_http_app=mcp_http_app))
app.include_router(router, prefix="/api")
app.mount("/api/mcp", mcp_http_app)
# OAuth discovery is served at the origin, outside the mounted MCP app.
app.router.routes.extend(
    create_protected_resource_routes(
        resource_url=mcp_config.resource_url,
        authorization_servers=[mcp_config.issuer_url],
    )
)

register_exception_handlers(app)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"], summary="Проверка доступности")
async def health() -> dict[str, str]:
    return {"status": "ok"}
