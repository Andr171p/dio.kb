from typing import Annotated

from fastapi import APIRouter, Query, status
from pydantic import HttpUrl

from src.api.dependencies.auth import require_auth_user
from src.api.dependencies.links import LinkPreview, link_preview_fetcher

router = APIRouter(prefix="/link-preview", tags=["Links"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    dependencies=[require_auth_user],
    summary="Превью внешней ссылки (OpenGraph)",
)
async def get_link_preview(url: Annotated[HttpUrl, Query(description="Адрес публичной страницы")]) -> LinkPreview:
    return await link_preview_fetcher.fetch(str(url))
