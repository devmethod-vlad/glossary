from typing import Literal
from uuid import UUID

from app.common.arbitrary_model import ArbitraryModel


class GlossaryElementResponse(ArbitraryModel):
    """Поля элемента глоссария"""

    id: UUID
    abbreviation: str
    term: str
    definition: str


class GlossaryElementsBulkCreateResponse(ArbitraryModel):
    """Ответ на создание элементов глоссария"""

    status: Literal["modified"]
    created: list[UUID]
    updated: list[UUID]


class GlossaryElementsGetResponse(ArbitraryModel):
    """Ответ на получение элементов глоссария"""

    count: int
    data: list[GlossaryElementResponse]


class GlossaryUpdateFromXlsxResponse(ArbitraryModel):
    """Ответ на обновление глоссария из xlsx"""

    status: Literal["modified"]
    parsing_error: bool = False
