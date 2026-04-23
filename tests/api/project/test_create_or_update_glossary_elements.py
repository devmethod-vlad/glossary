from uuid import uuid4

import httpx
from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import GlossaryElement
from app.services.interfaces import IGlossaryService


class TestCreateOrUpdateGlossaryElementsAPI:
    """Тест API создания/изменения элементов глоссария"""

    async def test_create_or_update_glossary_elements(
        self,
        client: httpx.AsyncClient,
        ten_glossary_elements: list[GlossaryElement],
        faker: Faker,
        glossary_service: IGlossaryService,
        db_session: AsyncSession,
    ) -> None:
        """Тест создания/изменения элементов глоссария"""
        glossary_elements_to_create = [
            {
                "id": str(uuid4()),
                "abbreviation": faker.pystr(min_chars=1, max_chars=500),
                "term": faker.pystr(min_chars=1),
                "definition": faker.pystr(min_chars=1),
            }
            for _ in range(5)
        ]
        glossary_elements_to_update = [
            {
                "id": str(element.id),
                "abbreviation": faker.pystr(min_chars=1, max_chars=500),
                "term": faker.pystr(min_chars=1),
                "definition": faker.pystr(min_chars=1),
            }
            for element in ten_glossary_elements
        ]
        response = await client.post(
            "/glossary",
            json=glossary_elements_to_create + glossary_elements_to_update,
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["updated"]) == 10
        assert len(data["created"]) == 5

        db_res = (await db_session.execute(select(GlossaryElement))).scalars().all()
        db_res_dicts = [
            {
                "id": str(row.id),
                "abbreviation": row.abbreviation,
                "term": row.term,
                "definition": row.definition,
            }
            for row in db_res
        ]

        assert db_res_dicts == glossary_elements_to_update + glossary_elements_to_create
