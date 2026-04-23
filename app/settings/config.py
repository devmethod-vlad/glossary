import datetime
from collections.abc import Sequence
from typing import Self

from pydantic import PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvBaseSettings(BaseSettings):
    """Базовый класс для прокидывания настроек из env"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class AppSettings(EnvBaseSettings):
    """Настройки приложения FastAPI"""

    mode: str = "DEV"
    host: str
    port: int
    debug_host: str | None = None
    debug_port: int | str | None = None
    workers_num: int
    access_key: str
    debug: bool = True
    root_path: str = ""
    glossary_attachments_page_id: str
    glossary_auth_token: str
    glossary_after_update_block_minutes: int
    glossary_update_timeout: int
    glossary_abbreviation_delimeter: str
    glossary_term_delimeter: str
    glossary_request_garbage_symbols: str
    request_edu_timeout: int
    prefix: str = ""
    wait_for_database_timeout: int = 20
    database_reconnect_timeout: int = 2
    logs_host_path: str
    logs_contr_path: str

    model_config = SettingsConfigDict(env_prefix="app_")


class PostgresSettings(EnvBaseSettings):
    """Настройки Postgres"""

    engine: str = "postgresql"
    host: str
    port: int
    user: str
    password: str
    db: str
    pool_size: int | None = None
    pool_overflow_size: int | None = None
    leader_usage_coefficient: float | None = None
    use_async: bool = True
    echo: bool = False
    autoflush: bool = False
    autocommit: bool = False
    expire_on_commit: bool = False
    engine_health_check_delay: int | None = None
    dsn: PostgresDsn | None = None
    slave_hosts: Sequence[str] | str = ""
    slave_dsns: Sequence[PostgresDsn] | str = ""

    @model_validator(mode="after")
    def assemble_db_connection(self) -> Self:
        """Сборка Postgres DSN"""
        if self.dsn is None:
            self.dsn = str(  # type: ignore
                PostgresDsn.build(
                    scheme=self.engine + "+asyncpg" if self.use_async else self.engine,
                    username=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port,
                    path=f"{self.db}",
                )
            )
        return self

    model_config = SettingsConfigDict(env_prefix="postgres_")


class RedisSettings(EnvBaseSettings):
    """Настройки Redis"""

    hostname: str
    port: int
    connect_timeout: int
    timeout: int
    database: int

    model_config = SettingsConfigDict(env_prefix="redis_")


class SchedulerSettings(EnvBaseSettings):
    """Настройки планировщика"""

    update_glossary_time: datetime.time
    logs_host_path: str
    logs_contr_path: str

    model_config = SettingsConfigDict(env_prefix="scheduler_")


class ARQSettings(EnvBaseSettings):
    """Настройки ARQ"""

    logs_host_path: str
    logs_contr_path: str

    model_config = SettingsConfigDict(env_prefix="arq_")


class Settings(EnvBaseSettings):
    """Настройки проекта"""

    app: AppSettings = AppSettings()
    scheduler: SchedulerSettings = SchedulerSettings()
    arq: ARQSettings = ARQSettings()
    database: PostgresSettings = PostgresSettings()
    redis: RedisSettings = RedisSettings()


settings = Settings()
