import asyncio
import traceback
from collections.abc import Awaitable, Callable
from typing import Any

from arq import Worker
from arq.connections import RedisSettings

from app.common.logger import GlossaryLogger, LoggerType
from app.infrastructure.background.instant.tasks import update_glossary_from_xlsx
from app.settings.config import settings

logger = GlossaryLogger(logger_type=LoggerType.ARQ)


class WorkerSettings:
    """Настройки воркера ARQ"""

    functions: list[Callable[..., Awaitable[Any]]] = [update_glossary_from_xlsx]
    redis_settings: RedisSettings = RedisSettings(
        host=settings.redis.hostname,
        port=settings.redis.port,
        database=settings.redis.database,
        conn_retries=0,
        conn_timeout=settings.redis.connect_timeout,
    )


async def main() -> None:
    """Запуск worker'а"""
    logger.info("Запуск Worker ARQ...")
    attempt_count = 0
    last_error_time = 0

    while True:
        try:
            worker: Worker = Worker(
                functions=WorkerSettings.functions, redis_settings=WorkerSettings.redis_settings
            )
            await worker.async_run()
        except Exception as e:
            attempt_count += 1
            current_time = int(asyncio.get_event_loop().time())

            logger.warning(
                f"Ошибка ARQ worker'а: ({type(e)}): {traceback.format_exc()}. Повторная попытка через 5 секунд... "
                f"(Попытка #{attempt_count})"
            )

            if current_time - last_error_time >= 60:
                logger.error(
                    f"Ошибка ARQ worker'а: ({type(e)}): {traceback.format_exc()}. Повторная попытка через 5 секунд... "
                )
                last_error_time = current_time

            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
