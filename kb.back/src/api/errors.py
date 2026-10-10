from typing import Any

import logging
from http import HTTPStatus

from ddf.application.exceptions import ApplicationError
from ddf.domain.exceptions import DomainError
from ddf.infra.database.sqlalchemy.utils import get_constraint_name, is_unique_violation
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


def _error_response(
    status_code: int, error_code: str, message: str | None, details: Any = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"errorCode": error_code.lower(), "message": message, "details": details},
    )


async def _handle_business_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApplicationError | DomainError)
    return _error_response(exc.status_code, exc.error_code, exc.message, exc.details)


async def _handle_integrity_error(_: Request, exc: Exception) -> JSONResponse:
    """Нарушения ограничений, обнаруженные при commit (уникальность и т.п.), — это конфликт, а не 500."""

    assert isinstance(exc, IntegrityError)
    if is_unique_violation(exc):
        return _error_response(
            HTTPStatus.CONFLICT,
            "unique_constraint_violation",
            "Resource already exists.",
            get_constraint_name(exc),
        )

    logger.warning("Integrity error: %s", exc.orig)
    return _error_response(HTTPStatus.CONFLICT, "integrity_violation", "Operation violates data integrity.")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApplicationError, _handle_business_error)
    app.add_exception_handler(DomainError, _handle_business_error)
    app.add_exception_handler(IntegrityError, _handle_integrity_error)


__all__ = ["register_exception_handlers"]
