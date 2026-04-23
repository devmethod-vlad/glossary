from uuid import UUID

from app.common.arbitrary_model import ArbitraryModel


class GlossaryElementCreateUpdateDTO(ArbitraryModel):
    """Схема создания элемента глоссария"""

    id: UUID
    abbreviation: str
    term: str
    definition: str


class GlossaryElementSchema(GlossaryElementCreateUpdateDTO):
    """Схема элемента глоссария"""


class ListGLossaryElements(ArbitraryModel):
    """Схема множества элемента глоссария"""

    elements: list[GlossaryElementSchema]
    count: int


class GlossaryElementsUpToDateData(ArbitraryModel):
    """Схема данных на обновление элементов глоссария"""

    raw_elements_to_delete: list[dict[str, str]]
    elements_to_create: list[GlossaryElementCreateUpdateDTO]
