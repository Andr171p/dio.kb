from ddf.domain.exceptions import InvalidStateError


class ArticleRevisionConflictError(InvalidStateError):
    error_code = "article_revision_conflict"
