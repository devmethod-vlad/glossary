import json
import uuid
from collections.abc import Callable

import aiofiles
import pytest
from faker import Faker
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.common.database import Database
from app.infrastructure.models import GlossaryElement

fake = Faker()


class GlossaryElementFactory(SQLAlchemyFactory[GlossaryElement]):
    """Фабрика проектов"""

    __model__ = GlossaryElement


@pytest.fixture()
def glossary_element_id() -> uuid.UUID:
    """Id банка вопросов"""
    return uuid.uuid4()


@pytest.fixture()
async def glossary_element_factory(db: Database):
    """Фикстура для проектов с возможностью переопределения полей"""

    async def create_glossary_element(**kwargs):
        glossary_element = GlossaryElementFactory.build(**kwargs)
        async with db.session_factory() as session:
            session.add(glossary_element)
            await session.commit()
        return glossary_element

    return create_glossary_element


@pytest.fixture()
async def glossary_element(
    glossary_element_id: uuid.UUID,
    glossary_element_factory: Callable,
    faker: Faker,
) -> GlossaryElement:
    """Фикстура элемента глоссария"""
    return await glossary_element_factory(
        id=glossary_element_id,
        abbreviation=faker.pystr(),
        term=faker.pystr(),
        definition=faker.pystr(),
    )


@pytest.fixture()
async def ten_glossary_elements(
    glossary_element_factory: Callable,
    faker: Faker,
) -> list[GlossaryElement]:
    """Фикстура 10 элементов глоссария"""
    return [
        await glossary_element_factory(
            id=uuid.uuid4(),
            abbreviation=faker.pystr(),
            term=faker.pystr(),
            definition=faker.pystr(),
        )
        for _ in range(10)
    ]


@pytest.fixture()
async def real_glossary_elements(
    db_session: Database,
) -> list[GlossaryElement]:
    """Фикстура реальных элементов глоссария"""
    async with aiofiles.open("tests/fixtures/real_glossary.json", encoding="utf-8") as file:
        content = await file.read()

    raw_elements = json.loads(content)

    for element in raw_elements:
        element["id"] = str(uuid.uuid4())

    result = await db_session.execute(
        GlossaryElement.__table__.insert().values(raw_elements).returning(GlossaryElement.__table__)
    )
    await db_session.commit()

    glossary_elements = [GlossaryElement(**row._asdict()) for row in result]

    return glossary_elements
