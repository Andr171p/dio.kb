"""ASGI-приложение DIOS Knowledge. Запуск: ``uvicorn src.main:app``."""

import logging

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from src.api.errors import register_exception_handlers  # noqa: E402
from src.api.lifespan import lifespan  # noqa: E402
from src.api.routers import router  # noqa: E402


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)

    app = FastAPI(title="DIOS Knowledge", version="0.1.0", lifespan=lifespan)
    app.include_router(router, prefix="/api")
    register_exception_handlers(app)

    @app.get("/health", tags=["Health"], summary="Проверка доступности")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
