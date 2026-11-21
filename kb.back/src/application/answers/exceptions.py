from http import HTTPStatus

from ddf.application.exceptions import ApplicationError


class AnswerNotFoundError(ApplicationError):
    status_code = HTTPStatus.NOT_FOUND
    error_code = "answer_not_found"


class AnswerAccessDeniedError(ApplicationError):
    status_code = HTTPStatus.FORBIDDEN
    error_code = "answer_access_denied"


class AnswerNotReadyError(ApplicationError):
    status_code = HTTPStatus.CONFLICT
    error_code = "answer_not_ready"


class InvalidGeneratedAnswerError(RuntimeError):
    """Structured output не прошёл citation/структурную валидацию."""


class AnswerAccessChangedError(RuntimeError):
    """Права на источники изменились во время или после генерации."""
    error_code = "access_changed"
