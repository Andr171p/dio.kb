from uuid import UUID

from pydantic import BaseModel, Field, PositiveInt


class DownloadMediaDTO(BaseModel):
    download_url: str = Field(description="Временный URL для прямого скачивания из S3")
    expires_in: PositiveInt = Field(description="Время действия в секундах")


class AttachmentDTO(BaseModel):
    id: UUID = Field(description="Уникальный ID файла")
    original_filename: str = Field(description="Оригинальное имя файла")
    mime_type: str = Field(description="MIME тип файла")
    size_bytes: PositiveInt = Field(description="Размер файла в байтах")
