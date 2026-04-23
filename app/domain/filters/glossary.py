from app.common.filters.filters import BaseFilter, StringFilter, UUIDFilter


class GlossaryElementFilter(BaseFilter):
    """Фильтр элементов глоссария"""

    id: UUIDFilter | None = None
    abbreviation: StringFilter | None = None
    term: StringFilter | None = None
    definition: StringFilter | None = None
