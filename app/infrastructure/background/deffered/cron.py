import datetime

from app.common.arbitrary_model import ArbitraryModel
from app.common.database import Database
from app.common.redis import RedisHelper
from app.infrastructure.background.deffered.tasks import (
    IBackgroundTask,
    TaskRequestUpdateGlossaryFromXlsx,
)
from app.infrastructure.unit_of_work.uow import UnitOfWork
from app.services.glossary import GlossaryService
from app.settings.config import settings


class Cron(ArbitraryModel):
    """Отложенная задача"""

    task: IBackgroundTask
    time: datetime.time | None


# Список отложенных задач
cron_list = [
    Cron(
        task=TaskRequestUpdateGlossaryFromXlsx(
            service=GlossaryService(
                uow=UnitOfWork(db=Database(config=settings.database)),
                redis=RedisHelper(config=settings.redis, database=settings.redis.database),
            )
        ),
        time=settings.scheduler.update_glossary_time,
    )
]
