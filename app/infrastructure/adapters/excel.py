from io import BytesIO

import numpy as np
import pandas as pd

from app.infrastructure.adapters.interfaces import IExcelAdapter


class ExcelAdapter(IExcelAdapter):
    """Адаптер Excel"""

    @classmethod
    def convert_xlsx_file_to_dataframe(
        cls, xlsx_file: BytesIO, mapping: dict[str, str] | None = None, sheet_name: int | str = 0
    ) -> pd.DataFrame:
        """Перевод BytesIO xlsx файла в pandas DataFrame"""
        df = (
            pd.read_excel(xlsx_file, sheet_name=sheet_name, engine="openpyxl")
            .replace(np.nan, "")
            .replace(r"^\s*$", "", regex=True)
        )

        if mapping:
            df.rename(columns=mapping, inplace=True)

        return df

    @classmethod
    def convert_dataframe_to_xlsx_file(cls, df: pd.DataFrame) -> BytesIO:
        """Перевод объекта pandas DataFrame в BytesIO xlsx файл"""
        excel_file = BytesIO()

        with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        excel_file.seek(0)

        return excel_file

    @classmethod
    def clean_up_df_and_identify_errors(cls, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Получение очищенного от ошибок DataFrame и возврат ошибок"""
        existings_problems_indexes = set()

        # пустые строки
        empty_rows_indexes = cls.get_empty_rows_indexes(df=df)
        existings_problems_indexes |= empty_rows_indexes

        # import time
        # time.sleep(5)

        # аббревиатуры > 500 символов
        long_abbreviations_indexes = cls.get_long_abbreviations_indexes(df=df)
        existings_problems_indexes |= long_abbreviations_indexes

        # заполнено только одно поле
        single_filled_columns_indexes = cls.get_only_one_field_indexes(df=df)
        existings_problems_indexes |= single_filled_columns_indexes

        # дубликаты
        duplicates_indexes = cls.get_duplicates_indexes(df=df)
        existings_problems_indexes |= duplicates_indexes

        problem_elements_dataframe = df.iloc[list(existings_problems_indexes)].copy()
        problem_elements_dataframe.insert(0, "№ строки", 0)
        problem_elements_dataframe.insert(1, "Тип ошибки", "")
        for idx, _row in problem_elements_dataframe.iterrows():
            problem_elements_dataframe.at[idx, "№ строки"] = idx + 2
            if idx in empty_rows_indexes:
                problem_elements_dataframe.at[idx, "Тип ошибки"] = "Пустая строка"
            elif idx in long_abbreviations_indexes:
                problem_elements_dataframe.at[idx, "Тип ошибки"] = (
                    "Аббревиатура длиннее 500 символов"
                )
            elif idx in single_filled_columns_indexes:
                problem_elements_dataframe.at[idx, "Тип ошибки"] = "Строка не заполнена полностью"
            elif idx in duplicates_indexes:
                problem_elements_dataframe.at[idx, "Тип ошибки"] = "Дубликат"

        problem_elements_dataframe = problem_elements_dataframe.sort_values(by="№ строки")
        problem_elements_dataframe.rename(
            columns={"abbreviation": "Аббревиатура", "term": "Термин", "definition": "Определение"},
            inplace=True,
        )
        problem_elements_dataframe.reset_index(drop=True, inplace=True)

        df.drop(df.index[list(existings_problems_indexes)], inplace=True)

        return df, problem_elements_dataframe

    @classmethod
    def get_empty_rows_indexes(cls, df: pd.DataFrame) -> set[int]:
        """Получение индексов пустых строк"""
        empty_rows = df[
            ((df["abbreviation"] == "") & (df["term"] == "") & (df["definition"] == ""))
        ]
        return set(empty_rows.index.tolist())

    @classmethod
    def get_long_abbreviations_indexes(cls, df: pd.DataFrame) -> set[int]:
        """Получение индексов строк с аббревиатурами, которые больше 500 символов"""
        long_abbreviations = df[(df["abbreviation"].astype(str).str.len() > 500)]
        return set(long_abbreviations.index.tolist())

    @classmethod
    def get_only_one_field_indexes(cls, df: pd.DataFrame) -> set[int]:
        """Получение индексов строк, где заполнено лишь одно поле из трёх"""
        single_filled_columns = df[
            ((df["abbreviation"] == "") & (df["term"] == "") & (df["definition"] == ""))
            | ((df["abbreviation"] != "") & (df["term"] == "") & (df["definition"] == ""))
            | ((df["abbreviation"] == "") & (df["term"] != "") & (df["definition"] == ""))
            | ((df["abbreviation"] == "") & (df["term"] == "") & (df["definition"] != ""))
        ]
        return set(single_filled_columns.index.tolist())

    @classmethod
    def get_duplicates_indexes(cls, df: pd.DataFrame) -> set[int]:
        """Получение индексов дубликатов строк (за исключением уникальных)"""
        duplicates = df.duplicated(subset=["abbreviation", "term", "definition"], keep="first")
        return set(duplicates[duplicates].index.tolist())
