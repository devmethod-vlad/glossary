from redis.asyncio import from_url
from redis.asyncio.client import Pipeline, Redis
from redis.exceptions import ConnectionError, TimeoutError

from app.common.exceptions.exceptions import RedisConnectionError
from app.settings.config import RedisSettings


class RedisHelper:
    """Вспомогательный класс для работы с Redis"""

    def __init__(self, config: RedisSettings, database: int):
        self.config: RedisSettings = config
        self.connection: Redis = from_url(
            f"redis://{config.hostname}:{config.port}/{database}",
            socket_connect_timeout=config.connect_timeout,
            socket_timeout=config.timeout,
            decode_responses=True,
        )

    async def pipe(self) -> Pipeline:
        """Получение redis pipeline с предварительной проверкой на доступ к redis"""
        try:
            await self.connection.ping()
        except (TimeoutError, ConnectionError):
            raise RedisConnectionError
        else:
            return self.connection.pipeline(transaction=True)
