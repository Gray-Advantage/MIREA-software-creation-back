from http import HTTPStatus

from httpx import AsyncClient

from tests.base import TestView


class TestPing(TestView):
    URL = "/api/ping"
    METHOD = "GET"

    async def test_success__returns_pong(self, client: AsyncClient) -> None:
        response = await self.request(client)

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"pong": "ok"}
