from http import HTTPStatus

from httpx import AsyncClient


async def test_get_company(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/company")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["email"] == "company@test.com"


async def test_patch_company(auth_client: AsyncClient) -> None:
    response = await auth_client.patch(
        "/api/company",
        json={"contact_name": "Обновлённый контакт"},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()["contact_name"] == "Обновлённый контакт"
