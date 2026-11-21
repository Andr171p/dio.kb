import asyncio
from functools import partial
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.indexing.config import ImageProcessingConfig, IndexingConfig, MarkdownChunkingConfig
from src.application.indexing.embeddings import embed_chunks
from src.application.indexing.image_analysis import ImageAnalysis, analyze_images
from src.application.indexing.models import MediaObject
from src.application.indexing.preparation import prepare_article_chunks
from src.application.indexing.types import PrepareArticleChunks
from src.application.indexing.utils import read_limited
from src.infra.aitunnel import AiTunnelConfig, AiTunnelImageAnalyzer, AiTunnelTextEmbedder
from src.infra.database.indexing import SqlAlchemyEmbeddingCache, SqlAlchemyImageAnalysisCache
from src.infra.services.media import SrvMediaClient, SrvMediaConfig, download_stream, validate_image

image_processing_config = ImageProcessingConfig()
indexing_config = IndexingConfig()
markdown_chunking_config = MarkdownChunkingConfig()

media_config = SrvMediaConfig()  # type: ignore[call-arg]
media_client = SrvMediaClient(media_config)

aitunnel_config = AiTunnelConfig()  # type: ignore[call-arg]
text_embedder = aitunnel_text_embedder = AiTunnelTextEmbedder(aitunnel_config)
image_analyzer = aitunnel_image_analyzer = AiTunnelImageAnalyzer(aitunnel_config)


def create_article_preparation(sessionmaker: async_sessionmaker[AsyncSession]) -> PrepareArticleChunks:
    """Собирает pipeline подготовки документов для индексации."""

    async def analyze_media(media_id: UUID) -> ImageAnalysis:
        async with asyncio.timeout(image_processing_config.analysis_timeout):
            attachment = await media_client.get_attachment(media_id)

            if attachment.size_bytes > image_processing_config.max_bytes:
                raise ValueError("Image exceeds maximum size")

            if not attachment.mime_type.startswith("image/"):
                raise ValueError("Unsupported media type")

            download = await media_client.create_download_url(media_id)
            content = read_limited(
                download_stream(download.download_url),
                max_bytes=image_processing_config.max_bytes,
            )

            await asyncio.to_thread(validate_image, content, image_processing_config.max_pixels)
            return await image_analyzer.analyze(MediaObject(content=content, content_type=attachment.mime_type))

    # Версия модели + версия подготовки входного изображения
    image_version = f"{image_analyzer.version}:{image_processing_config.analyzer_version or 'processing-v1'}"

    analyze = partial(
        analyze_images,
        analyze=analyze_media,
        cache=SqlAlchemyImageAnalysisCache(sessionmaker),
        analyzer_version=image_version,
        config=image_processing_config,
    )

    embed = partial(
        embed_chunks,
        embed_documents=text_embedder.embed_documents,
        cache=SqlAlchemyEmbeddingCache(sessionmaker),
        version=f"{aitunnel_config.embedding_model}:{text_embedder.dimensions}",
        batch_size=indexing_config.embedding_batch_size,
    )

    return partial(
        prepare_article_chunks,
        analyze=analyze,
        embed=embed,
        target_chars=markdown_chunking_config.target_chars,
    )
