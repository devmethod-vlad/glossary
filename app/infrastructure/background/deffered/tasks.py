import traceback
from abc import ABC, abstractmethod

from app.common.logger import GlossaryLogger, LoggerType
from app.services.interfaces import IGlossaryService

logger = GlossaryLogger(logger_type=LoggerType.SCHEDULER)


class IBackgroundTask(ABC):
    """Интерфейс отложенной задачи"""

    @abstractmethod
    async def run(self) -> None:
        """Запуск отложенной задачи"""


class TaskRequestUpdateGlossaryFromXlsx(IBackgroundTask):
    """Обновление глоссария из xlsx"""

    def __init__(self, service: IGlossaryService):
        self.service = service

    async def run(self) -> None:
        """Запуск отложенной задачи"""
        try:
            await self.service.update_glossary_from_xlsx(raise_blocked=False)
        except Exception as e:
            logger.error(f"Ошибка {type(e)}: {traceback.format_exc()}")
