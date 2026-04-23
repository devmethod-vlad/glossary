from sqlalchemy import text

from app.common.filters.filters import PaginationFilter
from app.common.repositories.repository import SQLAlchemyRepository
from app.domain.repositories.interfaces import IGlossaryElementRepository
from app.domain.schemas.glossary_element import GlossaryElementSchema, ListGLossaryElements
from app.infrastructure.models import GlossaryElement


class GlossaryElementRepository(SQLAlchemyRepository, IGlossaryElementRepository):
    """Репозиторий элементов глоссария"""

    model = GlossaryElement
    response_dto = GlossaryElementSchema

    async def get_glossary_elements_by_text(
        self, query: str, filters: PaginationFilter | None = None
    ) -> ListGLossaryElements:
        """Получение элементов глоссария по текстовому запросу"""
        query = self._escape_special_characters(query)
        sql_query = r"""
        WITH all_levels AS (
            SELECT *, CASE
                WHEN
                    -- Аббревиатуры с абсолютным совпадением
                    abbreviation_splitted ~ '^[^ ]+$' AND
                    abbreviation_splitted ILIKE :query
                    THEN 1
                WHEN
                    -- Термины с абсолютным совпадением
                    term_splitted ~ '^[^ ]+$' AND
                    term_splitted ILIKE :query
                    THEN 2
                WHEN
                    -- Аббревиатуры с частичным совпадением
                    :query ILIKE ANY(regexp_split_to_array(abbreviation_splitted, '\W+'))
                    THEN 3
                WHEN
                    -- Термины с частичным совпадением
                    :query ILIKE ANY(regexp_split_to_array(term_splitted, '\W+'))
                    THEN 4
                WHEN
                    -- Аббревиатуры с совпадением в начале фразы
                    abbreviation_splitted ILIKE :query || '%'
                    THEN 5
                WHEN
                    -- Термины с совпадением в начале фразы
                    term_splitted ILIKE :query || '%'
                    THEN 6
                WHEN
                    -- Аббревиатуры с совпадением внутри слова во фразе
                    abbreviation_splitted ILIKE '%' || :query || '%'
                    THEN 7
                WHEN
                    -- Термины с совпадением внутри слова во фразе
                    term_splitted ILIKE '%' || :query || '%'
                    THEN 8
            END AS rank_priority
            FROM ge_splitted
        )
        """
        sql_query += r"""
        SELECT id, abbreviation, term, definition, COUNT(*) OVER () AS total_count FROM
        -- Считаем количество встречаемых строк с одинаковым id, сортируя по этапу вывода (rank_priority)
        (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY id ORDER BY rank_priority) AS rn
            FROM all_levels
            WHERE rank_priority IS NOT NULL
        ) AS all_levels_counted
        -- Исключаем все, что встречаются в поиске более одного раза
        WHERE rn = 1
        ORDER BY
            rank_priority ASC,
            -- В этапах 1, 3, 5, 7 — сортировка по аббревиатуре
            -- В этапах 2, 4, 6, 8 — сортировка по термину
            CASE
                WHEN rank_priority IN (1, 3, 5, 7) THEN LOWER(abbreviation) COLLATE "C"
                ELSE LOWER(term) COLLATE "C"
            END ASC,
            CASE
                WHEN rank_priority IN (1, 3, 5, 7) THEN LOWER(term) COLLATE "C"
                ELSE LOWER(abbreviation) COLLATE "C"
            END ASC,
            LOWER(definition) COLLATE "C" ASC
        """
        if filters:
            if filters.limit:
                sql_query += r" LIMIT :limit"
            if filters.offset:
                sql_query += r" OFFSET :offset"

        result = await self.session.execute(
            text(sql_query),
            params={"query": query, "limit": filters.limit, "offset": filters.offset},
        )
        instances = result.mappings().all()

        return ListGLossaryElements(
            elements=self.to_dto(instances, dto=self.response_dto),
            count=instances[0]["total_count"] if instances else 0,
        )

    def _escape_special_characters(self, input_string: str) -> str:
        r"""Экранирует все специальные символы (% и _) для использования в SQL LIKE.
        Также экранирует сам символ экранирования (\), если он присутствует.
        """
        escaped = input_string.replace("\\", r"\\")
        escaped = escaped.replace("%", r"\%").replace("_", r"\_")
        return escaped
