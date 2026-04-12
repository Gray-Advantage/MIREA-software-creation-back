from http import HTTPStatus

import pytest
from starlette.testclient import TestClient


def test_lifespan_startup_and_shutdown_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.main.ensure_bucket", lambda: None)

    from api.main import app

    with TestClient(app) as client:
        response = client.get("/api/ping")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"pong": "ok"}
