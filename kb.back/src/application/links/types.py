from collections.abc import Awaitable, Callable

from .dtos import LinkPreview

type FetchLinkpreview = Callable[[str], Awaitable[LinkPreview]]
