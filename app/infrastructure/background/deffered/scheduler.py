import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.common.logger import GlossaryLogger, LoggerType
from app.infrastructure.background.deffered.cron import cron_list


async def main() -> None:
    """Планировщик"""
    logger = GlossaryLogger(logger_type=LoggerType.SCHEDULER)
    logger.info("Запуск планировщика ...")
    scheduler = AsyncIOScheduler()
    for cron in cron_list:
        logger.info(f"Запуск задачи {cron.task.__class__.__name__}")
        scheduler.add_job(
            func=cron.task.run,
            trigger="cron",
            hour=cron.time.hour,
            minute=cron.time.minute,
            replace_existing=True,
        )
    scheduler.start()

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
