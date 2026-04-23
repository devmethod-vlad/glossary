import contextlib
from io import BytesIO
from uuid import UUID, uuid4

import pandas as pd
from arq.connections import (
    RedisSettings as ArqRedisSettings,
    create_pool,
)

from app.api.v1.dto.requests.glossary import (
    GlossaryElementsBulkCreateRequest,
    GlossaryElementsGetRequest,
)
from app.api.v1.dto.responses.glossary import (
    GlossaryElementResponse,
    GlossaryElementsBulkCreateResponse,
    GlossaryElementsGetResponse,
    GlossaryUpdateFromXlsxResponse,
)
from app.common.exceptions.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    RedisConnectionError,
    RequestTimeoutError,
)
from app.common.filters.filters import (
    BaseFilter,
    Condition,
    PaginationFilter,
    StringFilter,
    UUIDFilter,
)
from app.common.redis import RedisHelper
from app.domain.exceptions import GlossaryUpdateFromXlsxError
from app.domain.filters.glossary import GlossaryElementFilter
from app.domain.schemas.glossary_element import (
    GlossaryElementCreateUpdateDTO,
    GlossaryElementSchema,
    GlossaryElementsUpToDateData,
    ListGLossaryElements,
)
from app.infrastructure.adapters.edu import EduAdapter
from app.infrastructure.adapters.excel import ExcelAdapter
from app.infrastructure.unit_of_work.interfaces import IUnitOfWork
from app.services.interfaces import IGlossaryService
from app.settings.config import settings


class GlossaryService(IGlossaryService):
    """Сервис глоссария"""

    def __init__(self, uow: IUnitOfWork, redis: RedisHelper):
        self.uow: IUnitOfWork = uow
        self.redis: RedisHelper = redis

    async def bulk_create_or_update_glossary_elements(
        self, request: GlossaryElementsBulkCreateRequest
    ) -> GlossaryElementsBulkCreateResponse:
        """Создание/изменение элементов глоссария"""
        async with self.uow:
            already_exist_elements: list[GlossaryElementSchema] = (
                await self.uow.glossary_element.get_list(
                    filters=BaseFilter(
                        condition=Condition.OR,
                        nested_filters=[
                            GlossaryElementFilter(
                                abbreviation=StringFilter(eq=element.abbreviation),
                                term=StringFilter(eq=element.term),
                                definition=StringFilter(eq=element.definition),
                            )
                            for element in request.elements
                        ],
                    )
                )
            )
            if already_exist_elements:
                raise AlreadyExistsError

            # try update
            updated_elements_ids: list[UUID] = []
            for element in request.elements:
                if not element.id:
                    continue

                with contextlib.suppress(NotFoundError):
                    updated_element: GlossaryElementSchema = await self.uow.glossary_element.update(
                        update_dto=GlossaryElementCreateUpdateDTO(
                            **element.model_dump(by_alias=True, exclude_none=True)
                        ),
                        filters=GlossaryElementFilter(id=UUIDFilter(eq=element.id)),
                    )
                    updated_elements_ids.append(updated_element.id)

            if len(updated_elements_ids) == len(request.elements):
                created_elements_ids = []
            else:
                created_elements: list[GlossaryElementSchema] = (
                    await self.uow.glossary_element.bulk_create(
                        bulk_create_dto=[
                            GlossaryElementCreateUpdateDTO(
                                id=element.id if element.id else uuid4(),
                                **element.model_dump(
                                    by_alias=True, exclude_none=True, exclude={"id"}
                                ),
                            )
                            for element in request.elements
                            if element.id not in updated_elements_ids  # won't create updated
                        ]
                    )
                )
                created_elements_ids: list[UUID] = [element.id for element in created_elements]

            await self.uow.commit()

        return GlossaryElementsBulkCreateResponse(
            status="modified", created=created_elements_ids, updated=updated_elements_ids
        )

    async def update_glossary_from_xlsx(
        self, raise_blocked: bool = True
    ) -> GlossaryUpdateFromXlsxResponse:
        """Актуализация глоссария из excel файла"""
        try:
            async with await self.redis.pipe() as pipe:
                # проверяем, можно ли обновлять
                status = (await pipe.get(name="glossary").execute())[0]
                if status == "updating" or raise_blocked and status == "blocked":
                    # нельзя
                    raise GlossaryUpdateFromXlsxError(status)
                else:
                    # можно
                    await pipe.set(name="glossary", value="updating").execute()

            xlsx_file = await EduAdapter.get_glossary_file_from_edu(
                page_id=settings.app.glossary_attachments_page_id,
                timeout=settings.app.request_edu_timeout,
                auth_token=settings.app.glossary_auth_token,
            )
            df_cleaned, df_errors = ExcelAdapter.clean_up_df_and_identify_errors(
                df=ExcelAdapter.convert_xlsx_file_to_dataframe(
                    xlsx_file=xlsx_file,
                    mapping={
                        "Аббревиатура": "abbreviation",
                        "Термин": "term",
                        "Определение": "definition",
                    },
                    sheet_name="Глоссарий",
                )
            )

            async with self.uow:
                # пытаемся обновить
                elements: list[GlossaryElementSchema] = await self.uow.glossary_element.get_list()
                up_to_date_data: GlossaryElementsUpToDateData = (
                    self._prepare_glossary_data_to_update(
                        elements_from_db=elements,
                        df_cleaned=df_cleaned,
                    )
                )

                if up_to_date_data.raw_elements_to_delete:
                    await self.uow.glossary_element.delete(
                        filters=BaseFilter(
                            condition=Condition.OR,
                            nested_filters=[
                                GlossaryElementFilter(
                                    abbreviation=StringFilter(eq=row["abbreviation"]),
                                    term=StringFilter(eq=row["term"]),
                                    definition=StringFilter(eq=row["definition"]),
                                )
                                for row in up_to_date_data.raw_elements_to_delete
                            ],
                        )
                    )

                if up_to_date_data.elements_to_create:
                    await self.uow.glossary_element.bulk_create(
                        bulk_create_dto=up_to_date_data.elements_to_create
                    )

                await self.uow.commit()

            if len(df_errors.index) != 0:
                xlsx_errors: BytesIO = ExcelAdapter.convert_dataframe_to_xlsx_file(df_errors)
                await EduAdapter.create_or_update_file_on_edu(
                    page_id=settings.app.glossary_attachments_page_id,
                    filename="ERRORS.xlsx",
                    file_data=xlsx_errors,
                    auth_token=settings.app.glossary_auth_token,
                    timeout=settings.app.request_edu_timeout,
                )

        except Exception as e:
            # не вышло
            if not isinstance(e, GlossaryUpdateFromXlsxError):
                await pipe.delete("glossary").execute()
            raise e
        else:
            # блокируем обновление
            if settings.app.glossary_after_update_block_minutes > 0:
                await pipe.set(
                    name="glossary",
                    value="blocked",
                    ex=settings.app.glossary_after_update_block_minutes * 60,
                ).execute()
            else:
                await pipe.delete("glossary").execute()

        return GlossaryUpdateFromXlsxResponse(
            status="modified",
            parsing_error=len(df_errors.index) != 0,
        )

    async def update_glossary_from_xlsx_detached(
        self,
    ) -> GlossaryUpdateFromXlsxResponse:
        """Актуализация глоссария из excel файла в фоновом режиме"""
        redis = await create_pool(
            ArqRedisSettings(
                host=settings.redis.hostname,
                port=settings.redis.port,
                database=settings.redis.database,
                conn_timeout=settings.redis.connect_timeout,
            )
        )
        try:
            job = await redis.enqueue_job("update_glossary_from_xlsx")
            if not job:
                raise RedisConnectionError

            result: GlossaryUpdateFromXlsxResponse = await job.result(
                timeout=settings.app.glossary_update_timeout
            )
            return result
        except TimeoutError:
            raise RequestTimeoutError

    async def get_glossary_elements(
        self, request: GlossaryElementsGetRequest
    ) -> GlossaryElementsGetResponse:
        """Получение элементов глоссария"""
        async with self.uow:
            glossary: ListGLossaryElements = (
                await self.uow.glossary_element.get_glossary_elements_by_text(
                    query=request.query,
                    filters=PaginationFilter(limit=request.limit, offset=request.offset),
                )
            )

        return GlossaryElementsGetResponse(
            count=glossary.count,
            data=[
                GlossaryElementResponse(**element.model_dump(by_alias=True, exclude_none=True))
                for element in glossary.elements
            ],
        )

    def _prepare_glossary_data_to_update(
        self, elements_from_db: list[GlossaryElementSchema], df_cleaned: pd.DataFrame
    ) -> GlossaryElementsUpToDateData:
        """Подготовка данных к обновлению глоссария"""
        fields = ["abbreviation", "term", "definition"]
        df_db = pd.DataFrame(
            [element.model_dump(by_alias=True, exclude_none=True) for element in elements_from_db],
            columns=["id"] + fields,
        )

        df_new = pd.merge(
            df_db,
            df_cleaned,
            on=fields,
            how="outer",
            indicator="Exist",
        )

        df_to_remove = df_new.loc[df_new["Exist"] == "left_only"][fields]
        df_to_add = df_new.loc[df_new["Exist"] == "right_only"][fields]

        raw_elements_to_delete: list[dict[str, str]] = [
            dict(**row) for row in df_to_remove.to_dict(orient="records")
        ]

        elements_to_create: list[GlossaryElementCreateUpdateDTO] = [
            GlossaryElementCreateUpdateDTO(
                id=uuid4(),
                **row,
            )
            for row in df_to_add.to_dict(orient="records")
        ]

        return GlossaryElementsUpToDateData(
            raw_elements_to_delete=raw_elements_to_delete, elements_to_create=elements_to_create
        )
