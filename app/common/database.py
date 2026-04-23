from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import DeclarativeMeta

from app.settings.config import PostgresSettings


class Database:
    """Вспомогательный класс для работы с БД"""

    def __init__(self, config: PostgresSettings):
        self.config = config
        self.engine = create_async_engine(url=str(self.config.dsn), echo=self.config.echo)

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=config.autoflush,
            autocommit=config.autocommit,
            expire_on_commit=config.expire_on_commit,
        )

        self.Base: DeclarativeMeta = automap_base()

    def prepare_tables(self) -> None:
        """Аккумуляция всех таблиц в self.Base"""
        sync_engine = create_engine(
            url=str(self.config.dsn).replace("postgresql+asyncpg", "postgresql")
        )
        self.Base.prepare(autoload_with=sync_engine)
        self.tables = dict(self.Base.classes)
