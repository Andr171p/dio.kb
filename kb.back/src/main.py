"""ASGI-приложение DIOS Knowledge. Запуск: ``uvicorn src.main:app``."""

import logging
from functools import partial

from fastapi import FastAPI, status

from src.api.exception_handlers import register_exception_handlers
from src.api.lifespan import lifespan
from src.api.routers import router
from src.api.routers.mcp import mcp, mcp_http_app, oauth_protected_resource_routes

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="DIOS Knowledge",
    version="0.1.0",
    lifespan=partial(lifespan, mcp=mcp),
    routes=oauth_protected_resource_routes,
)
app.include_router(router, prefix="/api")
app.mount("/api/mcp", mcp_http_app)

register_exception_handlers(app)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"], summary="Проверка доступности")
async def health() -> dict[str, str]:
    return {"status": "ok"}
