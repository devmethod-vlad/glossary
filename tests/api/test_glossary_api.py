import httpx

from app.infrastructure.models import GlossaryElement


class TestGlossaryGetElementsAPI:
    """Тесты API получения элементов глоссария с пагинацией."""

    async def test_getelements_default_params(
        self,
        client: httpx.AsyncClient,
        real_glossary_elements: list[GlossaryElement],
    ) -> None:
        """GET /glossary/getelements без параметров использует limit=100 и offset=0."""
        response = await client.get("/glossary/getelements")

        assert response.status_code == 200
        data = response.json()

        assert set(data.keys()) == {"data", "count", "total"}
        assert isinstance(data["data"], list)
        assert data["count"] == len(data["data"])
        assert data["total"] == len(real_glossary_elements)
        assert data["count"] <= 100

    async def test_getelements_validation(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        """Проверяет валидацию query-параметров limit/offset."""
        response_limit_too_big = await client.get("/glossary/getelements?limit=501")
        response_limit_zero = await client.get("/glossary/getelements?limit=0")
        response_offset_negative = await client.get("/glossary/getelements?offset=-1")

        assert response_limit_too_big.status_code == 422
        assert response_limit_zero.status_code == 422
        assert response_offset_negative.status_code == 422

    async def test_getelements_pagination(
        self,
        client: httpx.AsyncClient,
        glossary_element_factory,
    ) -> None:
        """Проверяет корректность страницы, count и total."""
        await glossary_element_factory(
            abbreviation="AAA",
            term="term-1",
            definition="definition-1",
        )
        await glossary_element_factory(
            abbreviation="BBB",
            term="term-2",
            definition="definition-2",
        )
        await glossary_element_factory(
            abbreviation="CCC",
            term="term-3",
            definition="definition-3",
        )

        response = await client.get("/glossary/getelements?limit=2&offset=1")

        assert response.status_code == 200
        data = response.json()
        assert [element["abbreviation"] for element in data["data"]] == ["BBB", "CCC"]
        assert data["count"] == 2
        assert data["total"] == 3
