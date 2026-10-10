from collections.abc import AsyncIterable
from uuid import UUID

import aiohttp

from src.application.search.models import MediaFile
from src.infra.services.base import SrvBaseClient

from .dtos import AttachmentDTO, DownloadMediaDTO

_S3_CONNECT_TIMEOUT = 60
_MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024


async def download_stream(url: str, chunk_size: int = 1024 * 64) -> AsyncIterable[bytes]:
    """Потоково скачивает файл из S3 по предподписанному URL."""

    timeout = aiohttp.ClientTimeout(connect=_S3_CONNECT_TIMEOUT)

    async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url) as response:
        response.raise_for_status()

        async for chunk in response.content.iter_chunked(chunk_size):
            yield chunk


class SrvMediaClient(SrvBaseClient):
    async def get_attachment(self, media_id: UUID) -> AttachmentDTO:
        async with (
            self._get_token_session() as session,
            session.get(f"/api/v1/attachments/{media_id}") as response,
        ):
            response.raise_for_status()
            data = await response.json()

        return AttachmentDTO.model_validate(data)

    async def create_download_url(self, media_id: UUID) -> DownloadMediaDTO:
        """Создаёт временный URL для скачивания объекта."""

        async with (
            self._get_token_session() as session,
            session.get(f"/api/v1/attachments/{media_id}/presigned-download") as response,
        ):
            response.raise_for_status()
            data = await response.json()

        return DownloadMediaDTO.model_validate(data)

    async def download(self, media_id: UUID) -> MediaFile:
        """Скачивает вложение целиком (реализация порта ``MediaStorage`` для индексации)."""

        attachment = await self.get_attachment(media_id)
        if attachment.size_bytes > _MAX_DOWNLOAD_BYTES:
            raise ValueError(
                f"Attachment {media_id} is too large for indexing: {attachment.size_bytes} bytes."
            )

        download = await self.create_download_url(media_id)
        content = bytearray()
        async for chunk in download_stream(download.download_url):
            content.extend(chunk)

        return MediaFile(content=bytes(content), content_type=attachment.mime_type)
