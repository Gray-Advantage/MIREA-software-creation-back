from typing import Any, Literal, LiteralString

import pytest
from httpx import AsyncClient, Response


class TestView:
    URL: LiteralString
    METHOD: Literal["GET", "POST", "DELETE", "PUT", "PATCH"]

    @pytest.fixture(autouse=True)
    def required_class_variables(self) -> None:
        assert getattr(self, "URL", None) is not None, "URL не указан!"
        assert getattr(self, "METHOD", None) is not None, "METHOD не указан!"

    async def request(
        self,
        client: AsyncClient,
        path: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Response:
        if path is None:
            path = {}
        return await client.request(
            self.METHOD,
            self.URL.format(**path),
            **kwargs,
        )
