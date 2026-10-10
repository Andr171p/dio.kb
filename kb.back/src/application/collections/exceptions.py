from http import HTTPStatus

from ddf.application.exceptions import ApplicationError


class CollectionTargetAlreadyPlacedError(ApplicationError):
    status_code = HTTPStatus.CONFLICT
    error_code = "collection_target_already_placed"
