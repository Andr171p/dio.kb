from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import HttpUrl

from src.api.dependencies.auth import CurrentUser
from src.api.dependencies.links import LinkPreviewFetcherDep
from src.application.links import usecases
from src.application.links.dtos import LinkPreview

router = APIRouter(prefix="/link-preview", tags=["Links"])


@router.get("", summary="Превью внешней ссылки (OpenGraph)")
async def get_link_preview(
    url: Annotated[HttpUrl, Query(description="Адрес публичной страницы")],
    _: CurrentUser,
    fetcher: LinkPreviewFetcherDep,
) -> LinkPreview:
    return await usecases.get_link_preview(str(url), fetcher=fetcher)
