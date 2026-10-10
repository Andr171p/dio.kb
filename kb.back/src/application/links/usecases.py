from .dtos import LinkPreviewResponse
from .protocols import LinkPreviewFetcher


async def get_link_preview(url: str, *, fetcher: LinkPreviewFetcher) -> LinkPreviewResponse:
    """Превью внешней ссылки для редактора и просмотра статьи."""

    return await fetcher.fetch(url)
