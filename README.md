# Глоссарий
<p>
    <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-009688.svg?style=flat&logo=FastAPI&logoColor=white"></a>
    <a href="https://github.com/postgres/postgres"><img src="https://img.shields.io/badge/PostgreSQL-%234169E1?logo=postgresql&logoColor=white"></a>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json"></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
    <a href="https://ollycope.com/software/yoyo/latest/"><img src="https://img.shields.io/badge/yoyo--migrations-blue?logoColor=%23285A87"></a>


</p>

Для запуска проекта файл `.env` должен содержать следующие параметры:

    COMPOSE_PATH_SEPARATOR=;
    COMPOSE_FILE=docker-compose.yml;docker-compose.dev.yml

    APP_MODE=...
    APP_HOST=...
    APP_PORT=...
    APP_DEBUG_HOST=...
    APP_DEBUG_PORT=...
    APP_WORKERS_NUM=...
    APP_ACCESS_KEY=...
    APP_GLOSSARY_ATTACHMENTS_PAGE_ID=...
    APP_GLOSSARY_AUTH_TOKEN=...
    APP_GLOSSARY_AFTER_UPDATE_BLOCK_MINUTES=...
    APP_GLOSSARY_UPDATE_TIMEOUT=30
    APP_GLOSSARY_ABBREVIATION_DELIMETER=","
    APP_GLOSSARY_TERM_DELIMETER=";"
    APP_GLOSSARY_REQUEST_GARBAGE_SYMBOLS=",;\n\t "
    APP_REQUEST_EDU_TIMEOUT=... # sec
    APP_PREFIX=/some/prefix
    APP_WAIT_FOR_DATABASE_TIMEOUT=20
    APP_DATABASE_RECONNECT_TIMEOUT=2
    APP_LOGS_HOST_PATH=./logs/app
    APP_LOGS_CONTR_PATH=/usr/src/logs/app

    SCHEDULER_UPDATE_GLOSSARY_TIME=... # hh:mm
    SCHEDULER_LOGS_HOST_PATH=./logs/scheduler
    SCHEDULER_LOGS_CONTR_PATH=/usr/src/logs/scheduler

    ARQ_LOGS_HOST_PATH=./logs/arq
    ARQ_LOGS_CONTR_PATH=/usr/src/logs/arq

    POSTGRES_USER=...
    POSTGRES_PASSWORD=...
    POSTGRES_HOST=...
    POSTGRES_PORT=...
    POSTGRES_HOST_PORT=...
    POSTGRES_DB=...

    REDIS_DATABASE=0
    REDIS_HOSTNAME=myredishost # or anything else
    REDIS_PORT=...
    REDIS_CONNECT_TIMEOUT=... # sec
    REDIS_TIMEOUT=... # sec

    REDISINSIGHT_PORT=...

    PGADMIN_DEFAULT_EMAIL=...
    PGADMIN_DEFAULT_PASSWORD=...
    PGADMIN_PORT=...

    GUNICORN_LOGS_HOST_PATH=...
    GUNICORN_LOGS_CONTR_PATH=...

Запуск проекта:

    docker compose up -d --build

##  Pre-commit и Ruff

Для использования Ruff:

    ruff check --fix

При выполнении команды с флагом --fix автоматически исправит мелкие недочеты вроде отступов и пробелов, порядка импортов

Для использования pre-commit:

Устанавливаем на компьютер через CMD

    pip install pre-commit

Внутри проекта в терминале IDE в установленном виртуальном окружении

    pre-commit install

Ожидаемый результат: pre-commit installed at .git\hooks\pre-commit

На случай обновлений периодически выполнять

    pre-commit autoupdate

Перед коммитом в терминале выполнить команду

    pre-commit run -a

Необходимо выполнять ее после правок до удачного прохождения всех стадий.
В случае невозможности на данном этапе привести все в порядок - закомментировать непроходимый этап в .pre-commit-config.yaml или удалить pre-commit

    pre-commit uninstall

Если правило форматирования в конкретном случае выполнить невозможно - сбоку от "проблемной строки" оставляем коммент вида '# noqa: <Код правила>'
