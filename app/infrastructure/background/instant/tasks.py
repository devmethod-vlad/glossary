import traceback

from app.api.v1.dto.responses.glossary import GlossaryUpdateFromXlsxResponse
from app.common.database import Database
from app.common.logger import GlossaryLogger, LoggerType
from app.common.redis import RedisHelper
from app.domain.exceptions import GlossaryUpdateFromXlsxError
from app.infrastructure.unit_of_work.uow import UnitOfWork
from app.services.glossary import GlossaryService
from app.settings.config import settings

logger = GlossaryLogger(logger_type=LoggerType.ARQ)


async def update_glossary_from_xlsx(ctx: dict) -> GlossaryUpdateFromXlsxResponse:
    """Задача для обновления глоссария из XLSX"""
    logger.info("Начало выполнения задачи 'update_glossary_from_xlsx'...")
    service = GlossaryService(
        uow=UnitOfWork(db=Database(config=settings.database)),
        redis=RedisHelper(config=settings.redis, database=settings.redis.database),
    )
    try:
        result: GlossaryUpdateFromXlsxResponse = await service.update_glossary_from_xlsx()
    except Exception as e:
        if not isinstance(e, GlossaryUpdateFromXlsxError):
            logger.error(f"Ошибка {type(e)}: {traceback.format_exc()}")
        raise e
    else:
        logger.info("Задача 'update_glossary_from_xlsx' выполнена")
        return result
