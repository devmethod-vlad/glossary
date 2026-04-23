from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.api.v1.dto.requests.glossary import (
    GlossaryElementRequest,
    GlossaryElementsBulkCreateRequest,
    GlossaryElementsGetRequest,
    GlossaryElementsListRequest,
)
from app.api.v1.dto.responses.glossary import (
    GlossaryElementsBulkCreateResponse,
    GlossaryElementsGetResponse,
    GlossaryElementsListResponse,
    GlossaryUpdateFromXlsxResponse,
)
from app.dependencies.dependencies import get_glossary_service
from app.services.interfaces import IGlossaryService

router = APIRouter(prefix="/glossary", tags=["Glossary"])


@router.post(
    "",
    response_model=GlossaryElementsBulkCreateResponse,
    summary="Создание/изменение элементов глоссария",
)
async def bulk_create_or_update_glossary_elements(
    glossary_elements: list[GlossaryElementRequest],
    service: Annotated[IGlossaryService, Depends(get_glossary_service)],
) -> JSONResponse:
    """Создание/изменение элементов глоссария"""
    result = await service.bulk_create_or_update_glossary_elements(
        request=GlossaryElementsBulkCreateRequest(elements=glossary_elements)
    )
    return JSONResponse(content=jsonable_encoder(result), status_code=200)


@router.post(
    "/all", response_model=GlossaryElementsGetResponse, summary="Получение элементов глоссария"
)
async def get_glossary_elements(
    glossary: GlossaryElementsGetRequest,
    service: Annotated[IGlossaryService, Depends(get_glossary_service)],
) -> JSONResponse:
    """Получение элементов глоссария"""
    result = await service.get_glossary_elements(request=glossary)
    return JSONResponse(content=jsonable_encoder(result), status_code=200)


@router.get(
    "/getelements",
    response_model=GlossaryElementsListResponse,
    summary="Получение всех элементов глоссария",
)
async def get_all_glossary_elements(
    request: Annotated[GlossaryElementsListRequest, Depends()],
    service: Annotated[IGlossaryService, Depends(get_glossary_service)],
) -> JSONResponse:
    """Получение всех элементов глоссария с пагинацией."""
    result = await service.get_all_glossary_elements(request=request)
    return JSONResponse(content=jsonable_encoder(result), status_code=200)


@router.get(
    "/excel",
    response_model=GlossaryUpdateFromXlsxResponse,
    summary="Актуализация глоссария из excel файла",
)
async def update_glossary_from_xlsx(
    service: Annotated[IGlossaryService, Depends(get_glossary_service)],
) -> JSONResponse:
    """Актуализация глоссария из excel файла"""
    result = await service.update_glossary_from_xlsx_detached()
    return JSONResponse(content=jsonable_encoder(result), status_code=200)
