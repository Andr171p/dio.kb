from typing import Annotated

from fastapi import Depends, Request

from src.application.links.protocols import LinkPreviewFetcher


def get_link_preview_fetcher(request: Request) -> LinkPreviewFetcher:
    return request.app.state.link_preview_fetcher


LinkPreviewFetcherDep = Annotated[LinkPreviewFetcher, Depends(get_link_preview_fetcher)]
