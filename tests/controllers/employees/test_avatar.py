import io
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from api.models import User
from tests.base import AuthTestView

TINY_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01"
    b"\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06"
    b"\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b"
    b"\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
    b"\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0"
    b"\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4"
    b"\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06"
    b"\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03"
    b"\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02"
    b'\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81'
    b"\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17"
    b"\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz"
    b"\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97"
    b"\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3"
    b"\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8"
    b"\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3"
    b"\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7"
    b"\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd2"
    b"\x8a(\x03\xff\xd9"
)

_S3 = "api.services.s3"


def _avatar_file(
    content: bytes = TINY_JPEG,
    content_type: str = "image/jpeg",
    filename: str = "avatar.jpg",
) -> dict:
    return {"file": (filename, io.BytesIO(content), content_type)}


class TestUploadAvatar(AuthTestView):
    URL = "/api/employees/{employee_id}/avatar"
    METHOD = "PUT"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client, path={"employee_id": 0})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @patch(f"{_S3}.upload", new_callable=AsyncMock)
    async def test_success__upload(
        self,
        mock_upload: AsyncMock,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await auth_client.put(
            f"/api/employees/{employee_user.id}/avatar",
            files=_avatar_file(),
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "avatar_url" in data
        assert f"/api/employees/{employee_user.id}/avatar" == data["avatar_url"]
        mock_upload.assert_awaited_once()

    @patch(f"{_S3}.delete", new_callable=AsyncMock)
    @patch(f"{_S3}.upload", new_callable=AsyncMock)
    async def test_success__replace(
        self,
        mock_upload: AsyncMock,
        mock_delete: AsyncMock,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        await auth_client.put(
            f"/api/employees/{employee_user.id}/avatar",
            files=_avatar_file(),
        )

        mock_upload.reset_mock()
        mock_delete.reset_mock()

        response = await auth_client.put(
            f"/api/employees/{employee_user.id}/avatar",
            files=_avatar_file(content_type="image/png", filename="new.png"),
        )

        assert response.status_code == HTTPStatus.OK
        mock_delete.assert_awaited_once()
        mock_upload.assert_awaited_once()

    async def test_error__employee_not_found(
        self,
        auth_client: AsyncClient,
    ) -> None:
        response = await auth_client.put(
            "/api/employees/99999/avatar",
            files=_avatar_file(),
        )
        assert response.status_code == HTTPStatus.NOT_FOUND


class TestGetAvatar(AuthTestView):
    URL = "/api/employees/{employee_id}/avatar"
    METHOD = "GET"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client, path={"employee_id": 0})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @patch(
        f"{_S3}.download",
        new_callable=AsyncMock,
        return_value=(TINY_JPEG, "image/jpeg"),
    )
    @patch(f"{_S3}.upload", new_callable=AsyncMock)
    async def test_success(
        self,
        mock_upload: AsyncMock,
        mock_download: AsyncMock,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        await auth_client.put(
            f"/api/employees/{employee_user.id}/avatar",
            files=_avatar_file(),
        )

        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "image/jpeg"
        assert response.content == TINY_JPEG

    async def test_error__no_avatar(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Avatar not found"}

    async def test_error__employee_not_found(
        self,
        auth_client: AsyncClient,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": 99999},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND


class TestDeleteAvatar(AuthTestView):
    URL = "/api/employees/{employee_id}/avatar"
    METHOD = "DELETE"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client, path={"employee_id": 0})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @patch(f"{_S3}.delete", new_callable=AsyncMock)
    @patch(f"{_S3}.upload", new_callable=AsyncMock)
    async def test_success(
        self,
        mock_upload: AsyncMock,
        mock_delete: AsyncMock,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        await auth_client.put(
            f"/api/employees/{employee_user.id}/avatar",
            files=_avatar_file(),
        )

        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
        )

        assert response.status_code == HTTPStatus.NO_CONTENT
        mock_delete.assert_awaited_once()

        get_resp = await auth_client.get(
            f"/api/employees/{employee_user.id}",
        )
        assert get_resp.json()["profile"]["avatar_url"] is None

    async def test_success__no_avatar_is_noop(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
        )

        assert response.status_code == HTTPStatus.NO_CONTENT


class TestDeleteEmployeeCleansAvatar(AuthTestView):
    URL = "/api/employees/{employee_id}"
    METHOD = "DELETE"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client, path={"employee_id": 0})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @patch(f"{_S3}.delete", new_callable=AsyncMock)
    @patch(f"{_S3}.upload", new_callable=AsyncMock)
    async def test_success__deletes_s3_object(
        self,
        mock_upload: AsyncMock,
        mock_delete: AsyncMock,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        await auth_client.put(
            f"/api/employees/{employee_user.id}/avatar",
            files=_avatar_file(),
        )

        mock_delete.reset_mock()

        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
        )

        assert response.status_code == HTTPStatus.NO_CONTENT
        mock_delete.assert_awaited_once()
