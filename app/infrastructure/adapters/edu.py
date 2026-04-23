from io import BytesIO
from zipfile import BadZipFile

import aiohttp
from openpyxl import load_workbook

from app.common.exceptions.exceptions import NotFoundError, RequestError, RequestTimeoutError
from app.infrastructure.adapters.interfaces import IEduAdapter


class EduAdapter(IEduAdapter):
    """Адаптер EDU"""

    @classmethod
    async def get_glossary_file_from_edu(
        cls, page_id: str, timeout: int, auth_token: str
    ) -> BytesIO:
        """Получение xlsx файла с EDU"""
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    f"https://edu.emias.ru/download/attachments/{page_id}/GLOSS.xlsx?api=v2",
                    timeout=timeout,
                    headers={
                        "X-Atlassian-Token": "no-check",
                        "Authorization": f"Bearer {auth_token}",
                    },
                ) as response,
            ):
                if response.status != 200:
                    raise RequestError(f"Сторонний сервис вернул статус - {response.status}")

                content_type = response.headers.get("Content-Type", "")
                if (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    not in content_type
                ):
                    raise RequestError(f"Некорректный Content-Type: {content_type}")

                xlsx_file = await response.content.read()
                try:
                    workbook = load_workbook(BytesIO(xlsx_file))
                    workbook.close()
                except BadZipFile:
                    raise RequestError("Файл не является корректным Excel-файлом")

                return BytesIO(xlsx_file)
        except (aiohttp.ClientConnectorError, TimeoutError) as e:
            if isinstance(e, aiohttp.ClientConnectorError):
                raise RequestError(str(e))
            if isinstance(e, TimeoutError):
                raise RequestTimeoutError

    @classmethod
    async def create_or_update_file_on_edu(
        cls, page_id: str, filename: str, file_data: BytesIO, auth_token: str, timeout: int
    ) -> None:
        """Создание/обновление файла на EDU"""
        try:
            attachment_id = await cls.get_attachment_id_from_edu(
                page_id, filename, auth_token, timeout=timeout
            )
        except NotFoundError:
            url = f"https://edu.emias.ru/rest/api/content/{page_id}/child/attachment"
        else:
            url = f"https://edu.emias.ru/rest/api/content/{page_id}/child/attachment/{attachment_id}/data"

        headers = {"X-Atlassian-Token": "no-check", "Authorization": f"Bearer {auth_token}"}

        form_data = aiohttp.FormData()
        form_data.add_field(
            "file",
            file_data.read(),
            filename=filename,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(url, headers=headers, data=form_data, timeout=timeout) as response,
            ):
                if response.status not in [200, 201]:
                    raise RequestError(f"Сторонний сервис вернул статус - {response.status}")
        except (aiohttp.ClientConnectorError, TimeoutError) as e:
            if isinstance(e, aiohttp.ClientConnectorError):
                raise RequestError(str(e))
            if isinstance(e, TimeoutError):
                raise RequestTimeoutError

    @classmethod
    async def get_attachment_id_from_edu(
        cls, page_id: str, filename: str, auth_token: str, timeout: int
    ) -> str:
        """Получение id вложения на EDU"""
        url = f"https://edu.emias.ru/rest/api/content/{page_id}/child/attachment"
        headers = {"Authorization": f"Bearer {auth_token}"}
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(url, headers=headers, timeout=timeout) as response,
            ):
                if response.status == 200:
                    data = await response.json()
                    for attachment in data["results"]:
                        if attachment["title"] == filename:
                            return attachment["id"]
                    raise NotFoundError
                else:
                    raise RequestError(f"Сторонний сервис вернул статус - {response.status}")
        except (aiohttp.ClientConnectorError, TimeoutError) as e:
            if isinstance(e, aiohttp.ClientConnectorError):
                raise RequestError(str(e))
            if isinstance(e, TimeoutError):
                raise RequestTimeoutError
