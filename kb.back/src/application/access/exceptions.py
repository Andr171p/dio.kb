from http import HTTPStatus

from ddf.application.exceptions import ApplicationError


class AccessDeniedError(ApplicationError):
    status_code = HTTPStatus.FORBIDDEN
    error_code = "access_denied"
