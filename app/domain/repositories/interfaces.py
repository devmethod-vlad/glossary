from abc import ABC, abstractmethod

from app.common.filters.filters import PaginationFilter
from app.common.repositories.interfaces import IRepository
from app.domain.schemas.glossary_element import ListGLossaryElements


class IGlossaryElementRepository(IRepository, ABC):
    """Интерфейс репозитория элементов глоссария"""

    @abstractmethod
    async def get_glossary_elements_by_text(
        self, query: str, filters: PaginationFilter | None = None
    ) -> ListGLossaryElements:
        """Получение элементов глоссария по текстовому запросу"""
