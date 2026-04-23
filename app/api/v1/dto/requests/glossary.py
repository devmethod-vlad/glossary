import re
from typing import Annotated, Self
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.common.arbitrary_model import ArbitraryModel
from app.domain.exceptions import GlossaryCreateError
from app.settings.config import settings


class GlossaryElementRequest(ArbitraryModel):
    """Поля элемента глоссария"""

    id: UUID | None = None  # None if create, uuid if update
    abbreviation: str | None = Field(default="", max_length=500)
    term: str | None = ""
    definition: str | None = ""

    @model_validator(mode="after")
    def minimum_two(self) -> Self:
        """Проверка на использование как минимум двух полей"""
        if bool(self.abbreviation) + bool(self.term) + bool(self.definition) < 2:
            raise GlossaryCreateError(
                "Нужно передать как минимум 2 поля из abbreviation, term, definition"
            )
        return self


class GlossaryElementsBulkCreateRequest(ArbitraryModel):
    """Запрос на создание элементов глоссария"""

    elements: list[GlossaryElementRequest]

    @model_validator(mode="after")
    def check_duplicates(self) -> Self:
        """Проверка на дубликаты"""
        raw_unique_elements = []
        for element in self.elements:
            if (element.abbreviation, element.term, element.definition) not in raw_unique_elements:
                raw_unique_elements.append((element.abbreviation, element.term, element.definition))
        if len(raw_unique_elements) != len(self.elements):
            raise GlossaryCreateError("Запрос содержит копии")

        return self


class GlossaryElementsGetRequest(ArbitraryModel):
    """Запрос на получение элементов глоссария"""

    query: Annotated[str, Field(min_length=1)]
    offset: int | None = 0
    limit: int | None = 25

    @field_validator("query", mode="after")
    @classmethod
    def remove_garbage_symbols(cls, query: str) -> str:
        """Очистка лишних символов по краям в запросе, очистка множественных пробелов"""
        query = query.strip(settings.app.glossary_request_garbage_symbols)
        query = re.sub(r"\s+", " ", query)
        return query
