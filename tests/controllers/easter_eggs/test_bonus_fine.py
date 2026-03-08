from http import HTTPStatus

from httpx import AsyncClient

from tests.base import TestView


class TestBonusDora(TestView):
    URL = "/bonus/dora"
    METHOD = "GET"

    async def test_success(self, client: AsyncClient) -> None:
        response = await self.request(client)

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "image/jpeg"
        assert len(response.content) > 0


class TestFineMem(TestView):
    URL = "/fine/mem"
    METHOD = "GET"

    async def test_success(self, client: AsyncClient) -> None:
        response = await self.request(client)

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "image/jpeg"
        assert len(response.content) > 0
