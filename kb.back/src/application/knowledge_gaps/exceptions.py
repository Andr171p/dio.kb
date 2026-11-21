from http import HTTPStatus

from ddf.application.exceptions import ApplicationError


class KnowledgeGapNotFoundError(ApplicationError):
    status_code = HTTPStatus.NOT_FOUND
    error_code = "knowledge_gap_not_found"


class KnowledgeGapAccessDeniedError(ApplicationError):
    status_code = HTTPStatus.FORBIDDEN
    error_code = "knowledge_gap_access_denied"
