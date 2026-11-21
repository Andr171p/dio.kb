from ddf.infra.database.sqlalchemy import PostgresConfig
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def create_database(config: PostgresConfig) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        config.uri,
        pool_size=config.pool_resize,
        max_overflow=config.max_overflow,
        pool_timeout=config.pool_timeout,
        pool_pre_ping=True,
        echo=config.echo,
    )
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    return engine, sessionmaker
