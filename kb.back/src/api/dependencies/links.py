from src.application.links.config import LinkPreviewConfig
from src.application.links.dtos import LinkPreview
from src.application.links.types import FetchLinkpreview
from src.infra.links.http import HttpLinkPreviewFetcher

link_preview_config = LinkPreviewConfig()
link_preview_fetcher = HttpLinkPreviewFetcher(link_preview_config)

__all__ = ["FetchLinkpreview", "LinkPreview", "link_preview_fetcher"]
