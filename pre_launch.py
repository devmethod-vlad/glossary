import argparse
import asyncio
import time
import traceback

from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists
from yoyo import get_backend, read_migrations
from yoyo.backends import DatabaseBackend
from yoyo.migrations import MigrationList

from app.common.database import Database
from app.common.logger import GlossaryLogger, LoggerType
from app.common.redis import RedisHelper
from app.settings.config import PostgresSettings, settings


def wait_for_db(logger: GlossaryLogger) -> None:
    """Ожидание базы данных, создание в случае отсутствия"""
    pg_settings = PostgresSettings(use_async=False)
    start_time = time.time()

    while True:
        try:
            engine = create_engine(str(pg_settings.dsn))
            if not database_exists(engine.url):
                logger.warning(f"База данных {pg_settings.db} не найдена. Создание...")
                create_database(engine.url)
                logger.info(f"База данных {pg_settings.db} успешно создана.")
            connection = engine.connect()
            break
        except Exception as e:
            elapsed_time = time.time() - start_time
            if elapsed_time >= settings.app.wait_for_database_timeout:
                error_str = f"Тайм-аут ({settings.app.wait_for_database_timeout} сек.). Сервер PostgreSQL не доступен."
                logger.error(error_str)
                raise TimeoutError(error_str)
            else:
                logger.warning(
                    f"Попытка подключения к базе данных провалилась: ({type(e)}): {traceback.format_exc()}. "
                    "Ожидание повторного подключения..."
                )
                time.sleep(settings.app.database_reconnect_timeout)

    connection.close()


def migrate() -> None:
    """Применение миграций"""
    pg_settings = PostgresSettings(use_async=False)

    backend: DatabaseBackend = get_backend(str(pg_settings.dsn))
    migrations: MigrationList = read_migrations("app/infrastructure/migrations")

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


def update_glossary() -> None:
    """Обновление глоссария"""
    from app.infrastructure.unit_of_work.uow import UnitOfWork  # noqa: PLC0415
    from app.services.glossary import GlossaryService  # noqa: PLC0415

    service = GlossaryService(
        uow=UnitOfWork(db=Database(config=settings.database)),
        redis=RedisHelper(config=settings.redis, database=settings.redis.database),
    )

    asyncio.run(service.update_glossary_from_xlsx(raise_blocked=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--logtype", help="Тип логирования", required=True, choices=["app", "scheduler", "arq"]
    )
    parser.add_argument("--wait-for-db", help="Ожидание БД", action="store_true")
    parser.add_argument("--migrate", help="Применение миграций", action="store_true")
    parser.add_argument(
        "--update-glossary", help="Обновление глоссария", choices=["silent", "strict"]
    )
    args = parser.parse_args()

    try:
        if args.migrate and not args.wait_for_db:
            raise argparse.ArgumentError(None, "--migrate требует использования --wait-for-db.")

        if args.update_glossary and not args.migrate:
            raise argparse.ArgumentError(None, "--update-glossary требует использования --migrate.")

    except argparse.ArgumentError as e:
        parser.error(str(e))

    logger = GlossaryLogger(logger_type=LoggerType(args.logtype))
    logger.info("Запуск приложения...")
    time.sleep(2)

    if args.wait_for_db:
        logger.info("Ожидание базы данных...")
        try:
            wait_for_db(logger)
        except Exception as e:
            logger.error(f"Ошибка при ожидании базы данных: ({type(e)}): {traceback.format_exc()}")
            raise e

    if args.migrate:
        logger.info("Применение миграций...")
        try:
            migrate()
        except Exception as e:
            logger.error(f"Ошибка при применении миграций: ({type(e)}): {traceback.format_exc()}")
            raise e

    if args.update_glossary:
        logger.info("Обновление глоссария...")
        try:
            update_glossary()
        except Exception as e:
            error_str = f"Ошибка при обновлении глоссария: ({type(e)}): {traceback.format_exc()}"
            if args.update_glossary == "strict":
                logger.error(error_str)
                raise e
            elif args.update_glossary == "silent":
                logger.warning(error_str)
