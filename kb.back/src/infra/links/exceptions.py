
class UnsafeLinkError(Exception):
    """URL не соответствует политике публичных HTTP-запросов."""


class LinkPreviewUnavailableError(Exception):
    """Страница недоступна или не содержит поддерживаемый HTML."""
