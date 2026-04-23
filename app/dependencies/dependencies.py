from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from app.common.auth import AccessBearer
from app.common.database import Database
from app.common.redis import RedisHelper
from app.infrastructure.unit_of_work.interfaces import IUnitOfWork
from app.infrastructure.unit_of_work.uow import UnitOfWork
from app.services.glossary import GlossaryService
from app.services.interfaces import IGlossaryService
from app.settings.config import settings


async def get_db() -> AsyncGenerator[Database, None]:
    """Инициализация базы данных"""
    yield Database(config=settings.database)


async def get_redis() -> AsyncGenerator[RedisHelper, None]:
    """Инициализация redis"""
    yield RedisHelper(config=settings.redis, database=settings.redis.database)


async def get_uow(db: Annotated[Database, Depends(get_db)]) -> AsyncGenerator[IUnitOfWork, None]:
    """Зависимость, возвращающая UOW"""
    yield UnitOfWork(db)


def get_access_bearer() -> AccessBearer:
    """Зависимость, возвращающая Access Bearer"""
    return AccessBearer()


async def get_glossary_service(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
    redis: Annotated[RedisHelper, Depends(get_redis)],
) -> AsyncGenerator[IGlossaryService, None]:
    """Зависимость, возвращающая сервис глоссария"""
    yield GlossaryService(uow, redis)
