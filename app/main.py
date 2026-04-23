from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.types import Lifespan

from app.api.v1.glossary import router as glossary_router
from app.common.redis import RedisHelper
from app.common.version import get_app_info
from app.domain.exception_handler import exception_config
from app.settings.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Lifespan[FastAPI]]:
    """Удаление ключа glossary перед запуском приложения"""
    redis = RedisHelper(config=settings.redis, database=settings.redis.database)
    async with await redis.pipe() as pipe:
        await pipe.delete("glossary").execute()
    yield


app = FastAPI(title="Glossary API", root_path=f"{settings.app.prefix}", lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def redirect_to_docs() -> RedirectResponse:
    """Редирект на документацию"""
    return RedirectResponse(url=f"{settings.app.prefix}/docs")


@app.options("/{path:path}", include_in_schema=False)
async def preflight_handler() -> Response:
    """Проверка"""
    return Response(status_code=200)


@app.get("/healthcheck")
async def healthcheck() -> JSONResponse:
    """Проверка здоровья"""
    return JSONResponse(content=jsonable_encoder({"status": "ok"}), status_code=200)


@app.get("/version")
async def version() -> JSONResponse:
    """Версия приложения"""
    return JSONResponse(content=jsonable_encoder(get_app_info()), status_code=200)


app.include_router(glossary_router)

for exception, handler in exception_config.items():
    app.add_exception_handler(exception, handler)
