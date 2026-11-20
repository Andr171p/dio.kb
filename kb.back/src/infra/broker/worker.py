import asyncio
from functools import partial
from uuid import UUID

from ddf.infra.database.sqlalchemy import PostgresConfig
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from taskiq import TaskiqEvents, TaskiqState

from src.application.indexing.config import ImageProcessingConfig, IndexingConfig, MarkdownChunkingConfig
from src.application.indexing.embeddings import embed_chunks
from src.application.indexing.image_analysis import ImageAnalysis, analyze_images
from src.application.indexing.models import MediaObject
from src.application.indexing.preparation import prepare_article_chunks
from src.application.indexing.utils import read_limited
from src.infra.aitunnel import AiTunnelConfig, AiTunnelImageAnalyzer, AiTunnelTextEmbedder
from src.infra.broker.broker import broker
from src.infra.database.repositories.indexing import (
    SqlAlchemyEmbeddingCache,
    SqlAlchemyImageAnalysisCache,
    SqlAlchemyIndexingRepository,
)
from src.infra.qdrant import QdrantConfig, QdrantSearchIndex
from src.infra.services.media import SrvMediaClient, SrvMediaConfig, download_stream
from src.infra.services.media.images import validate_image


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    db_config = PostgresConfig()
    engine = create_async_engine(
        db_config.uri,
        pool_size=db_config.pool_resize,
        max_overflow=db_config.max_overflow,
        pool_timeout=db_config.pool_timeout,
        pool_pre_ping=True,
        echo=db_config.echo,
    )
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    ai_config = AiTunnelConfig()  # type: ignore[call-arg]
    embedder = AiTunnelTextEmbedder(ai_config)
    analyzer = AiTunnelImageAnalyzer(ai_config)
    media = SrvMediaClient(SrvMediaConfig())  # type: ignore[call-arg]
    indexing_config = IndexingConfig()
    index = QdrantSearchIndex(QdrantConfig(), write_batch_size=indexing_config.index_write_batch_size)
    image_config = ImageProcessingConfig()
    markdown_config = MarkdownChunkingConfig()

    async def analyze_media(media_id: UUID) -> ImageAnalysis:
        attachment = await media.get_attachment(media_id)
        if attachment.size_bytes > image_config.max_bytes or not attachment.mime_type.startswith("image/"):
            raise ValueError("Unsupported or oversized image")
        download = await media.create_download_url(media_id)
        content = await read_limited(download_stream(download.download_url), max_bytes=image_config.max_bytes)
        await asyncio.to_thread(validate_image, content, image_config.max_pixels)
        async with asyncio.timeout(image_config.analysis_timeout):
            return await analyzer.analyze(MediaObject(content=content, content_type=attachment.mime_type))

    analyze = partial(
        analyze_images,
        analyze=analyze_media,
        cache=SqlAlchemyImageAnalysisCache(sessionmaker),
        analyzer_version=analyzer.version,
        config=image_config,
    )
    embed = partial(
        embed_chunks,
        embed_documents=embedder.embed_documents,
        cache=SqlAlchemyEmbeddingCache(sessionmaker),
        version=f"{ai_config.embedding_model}:{ai_config.embedding_dimensions}",
        batch_size=indexing_config.embedding_batch_size,
    )
    state.prepare = partial(
        prepare_article_chunks, analyze=analyze, embed=embed, target_chars=markdown_config.target_chars
    )
    state.repository = SqlAlchemyIndexingRepository(sessionmaker)
    state.engine = engine
    state.embedder = embedder
    state.analyzer = analyzer
    state.media = media
    state.index = index
    await index.ensure_collection(embedder.dimensions)


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    await state.media.close()
    await state.analyzer.close()
    await state.embedder.close()
    await state.index.close()
    await state.engine.dispose()
