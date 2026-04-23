import abc
from io import BytesIO

import pandas as pd


class IExcelAdapter(abc.ABC):
    """Интерфейс адаптера Excel"""

    @classmethod
    @abc.abstractmethod
    def convert_xlsx_file_to_dataframe(
        cls, xlsx_file: BytesIO, mapping: dict[str, str] | None = None, sheet_name: int | str = 0
    ) -> pd.DataFrame:
        """Перевод BytesIO xlsx файла в pandas DataFrame"""

    @classmethod
    @abc.abstractmethod
    def convert_dataframe_to_xlsx_file(cls, df: pd.DataFrame) -> BytesIO:
        """Перевод объекта pandas DataFrame в BytesIO xlsx файл"""

    @classmethod
    @abc.abstractmethod
    def clean_up_df_and_identify_errors(cls, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Получение очищенного от ошибок DataFrame и возврат ошибок"""

    @classmethod
    @abc.abstractmethod
    def get_empty_rows_indexes(cls, df: pd.DataFrame) -> set[int]:
        """Получение индексов пустых строк"""

    @classmethod
    @abc.abstractmethod
    def get_long_abbreviations_indexes(cls, df: pd.DataFrame) -> set[int]:
        """Получение индексов строк с аббревиатурами, которые больше 500 символов"""

    @classmethod
    @abc.abstractmethod
    def get_only_one_field_indexes(cls, df: pd.DataFrame) -> set[int]:
        """Получение индексов строк, где заполнено лишь одно поле из трёх"""

    @classmethod
    @abc.abstractmethod
    def get_duplicates_indexes(cls, df: pd.DataFrame) -> set[int]:
        """Получение индексов дубликатов строк (за исключением уникальных)"""


class IEduAdapter(abc.ABC):
    """Интерфейс адаптера EDU"""

    @classmethod
    @abc.abstractmethod
    async def get_glossary_file_from_edu(cls, page_id: str, auth_token: str) -> BytesIO:
        """Получение xlsx файла с EDU"""

    @classmethod
    @abc.abstractmethod
    async def create_or_update_file_on_edu(
        cls, page_id: str, filename: str, file_data: BytesIO, auth_token: str
    ) -> None:
        """Создание/обновление файла на EDU"""

    @classmethod
    @abc.abstractmethod
    async def get_attachment_id_from_edu(cls, page_id: str, filename: str, auth_token: str) -> str:
        """Получение id вложения на EDU"""
