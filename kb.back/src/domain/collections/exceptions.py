from ddf.domain.exceptions import InvalidStateError, InvariantViolationError


class CollectionSelfPlacementError(InvariantViolationError):
    error_code = "collection_self_placement"


class CrossSpacePlacementError(InvariantViolationError):
    error_code = "cross_space_placement"


class CollectionCycleError(InvariantViolationError):
    """Размещение образует цикл в дереве коллекций."""

    error_code = "collection_cycle"


class CollectionNotEmptyError(InvalidStateError):
    error_code = "collection_not_empty"
