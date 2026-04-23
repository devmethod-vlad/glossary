from abc import ABC, abstractmethod

from app.api.v1.dto.requests.glossary import (
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


class IGlossaryService(ABC):
    """Интерфейс сервиса глоссария"""

    @abstractmethod
    async def bulk_create_or_update_glossary_elements(
        self, request: GlossaryElementsBulkCreateRequest
    ) -> GlossaryElementsBulkCreateResponse:
        """Создание/изменение элементов глоссария"""

    @abstractmethod
    async def get_glossary_elements(
        self, request: GlossaryElementsGetRequest
    ) -> GlossaryElementsGetResponse:
        """Получение элементов глоссария"""

    @abstractmethod
    async def get_all_glossary_elements(
        self, request: GlossaryElementsListRequest
    ) -> GlossaryElementsListResponse:
        """Получение всех элементов глоссария с пагинацией"""

    @abstractmethod
    async def update_glossary_from_xlsx(
        self, raise_blocked: bool
    ) -> GlossaryUpdateFromXlsxResponse:
        """Актуализация глоссария из excel файла"""

    @abstractmethod
    async def update_glossary_from_xlsx_detached(
        self,
    ) -> GlossaryUpdateFromXlsxResponse:
        """Актуализация глоссария из excel файла в фоновом режиме"""
