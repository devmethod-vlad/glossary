import traceback

from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.exceptions.exceptions import (
    AlreadyExistsError,
    ConflictError,
    LoginError,
    NotFoundError,
    RedisConnectionError,
    RequestError,
    RequestTimeoutError,
)
from app.common.logger import GlossaryLogger, LoggerType
from app.domain.exceptions import GlossaryCreateError, GlossaryUpdateFromXlsxError


def log_error(e: Exception) -> None:
    """Логирование ошибки"""
    logger = GlossaryLogger(logger_type=LoggerType.APP)
    logger.error(f"Ошибка {type(e)}: {traceback.format_exc()}")


async def validation_exception_handler(
    request: Request, exception: RequestValidationError
) -> JSONResponse:
    """Обработчик ошибки валидации"""
    # log_error(exception)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exception.errors()},
    )


async def login_exception_handler(request: Request, exception: LoginError) -> JSONResponse:
    """Обработчик ошибки авторизации"""
    # log_error(exception)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exception.args[0]},
    )


async def not_found_exception_handler(request: Request, exception: NotFoundError) -> JSONResponse:
    """Обработчик NotFoundError"""
    # log_error(exception)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Not found error"},
    )


async def already_exists_exception_handler(
    request: Request, exception: AlreadyExistsError
) -> JSONResponse:
    """Обработчик AlreadyExistsError"""
    # log_error(exception)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Already exist error"},
    )


async def conflict_exception_handler(request: Request, exception: ConflictError) -> JSONResponse:
    """Обработчик ConflictError"""
    log_error(exception)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": f"Conflict error {exception.args}"},
    )


async def request_exception_handler(request: Request, exception: RequestError) -> JSONResponse:
    """Обработчик RequestError"""
    log_error(exception)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Не удаётся совершить запрос на сторонний ресурс"},
    )


async def request_timeout_exception_handler(
    request: Request, exception: RequestError
) -> JSONResponse:
    """Обработчик RequestTimeoutError"""
    log_error(exception)
    return JSONResponse(
        status_code=status.HTTP_408_REQUEST_TIMEOUT,
        content={"detail": "Время ожидания истекло"},
    )


async def redis_connection_exception_handler(
    request: Request, exception: RedisConnectionError
) -> JSONResponse:
    """Обработчик RedisConnectionError"""
    log_error(exception)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Не удаётся подключиться к Redis"},
    )


async def glossary_update_from_xlsx_exception_handler(
    request: Request, exception: GlossaryUpdateFromXlsxError
) -> JSONResponse:
    """Обработчик GlossaryUpdateFromXlsxError"""
    # log_error(exception)
    return JSONResponse(
        status_code=status.HTTP_423_LOCKED,
        content={"detail": "Не удаётся обновить глоссарий в данный момент"},
    )


async def glossary_create_exception_handler(
    request: Request, exception: GlossaryCreateError
) -> JSONResponse:
    """Обработчик GlossaryCreateError"""
    log_error(exception)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": f"Не удаётся создать элементы глоссария: {exception.args[0]}"},
    )


async def any_exception_handler(request: Request, exception: Exception) -> Response:
    """Обработчик Exception"""
    log_error(exception)
    return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


exception_config = {
    RequestValidationError: validation_exception_handler,
    LoginError: login_exception_handler,
    NotFoundError: not_found_exception_handler,
    AlreadyExistsError: already_exists_exception_handler,
    RequestError: request_exception_handler,
    RequestTimeoutError: request_timeout_exception_handler,
    RedisConnectionError: redis_connection_exception_handler,
    ConflictError: conflict_exception_handler,
    GlossaryUpdateFromXlsxError: glossary_update_from_xlsx_exception_handler,
    GlossaryCreateError: glossary_create_exception_handler,
    Exception: any_exception_handler,
}
