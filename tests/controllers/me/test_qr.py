import uuid
from http import HTTPStatus

import httpx
from fakeredis import FakeAsyncRedis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Company, User
from api.services.auth import hash_password
from api.services.session_store import create_session


async def test_qr_active_false_when_no_session(
    admin_client: AsyncClient,
) -> None:
    r = await admin_client.get("/api/qr/active")
    assert r.status_code == HTTPStatus.OK
    assert r.json()["active"] is False


async def test_qr_generate_and_active(
    admin_client: AsyncClient,
) -> None:
    gen = await admin_client.post("/api/qr/generate")
    assert gen.status_code == HTTPStatus.OK
    token = gen.json()["token"]

    active = await admin_client.get("/api/qr/active")
    assert active.status_code == HTTPStatus.OK
    assert active.json()["active"] is True
    assert active.json()["token"] == token


async def test_qr_generate_deactivates_previous(
    admin_client: AsyncClient,
) -> None:
    await admin_client.post("/api/qr/generate")
    second = await admin_client.post("/api/qr/generate")
    assert second.status_code == HTTPStatus.OK


async def test_qr_scan_check_in_and_check_out(
    admin_client: AsyncClient,
    employee_client: AsyncClient,
) -> None:
    gen = await admin_client.post("/api/qr/generate")
    token = gen.json()["token"]

    first = await employee_client.post(
        "/api/qr/scan",
        json={"token": token},
    )
    assert first.status_code == HTTPStatus.OK
    assert first.json()["action"] == "check_in"

    second = await employee_client.post(
        "/api/qr/scan",
        json={"token": token},
    )
    assert second.status_code == HTTPStatus.OK
    assert second.json()["action"] == "check_out"


async def test_qr_scan_invalid_token_format(
    employee_client: AsyncClient,
) -> None:
    r = await employee_client.post("/api/qr/scan", json={"token": "not-a-uuid"})
    assert r.status_code == HTTPStatus.BAD_REQUEST


async def test_qr_scan_wrong_or_expired_token(
    employee_client: AsyncClient,
) -> None:
    r = await employee_client.post(
        "/api/qr/scan",
        json={"token": "00000000-0000-0000-0000-000000000000"},
    )
    assert r.status_code == HTTPStatus.BAD_REQUEST


async def test_qr_scan_profile_not_found(
    admin_client: AsyncClient,
    session: AsyncSession,
    company: Company,
    transport: ASGITransport,
    fake_redis_client: FakeAsyncRedis,
) -> None:
    gen = await admin_client.post("/api/qr/generate")
    token = gen.json()["token"]

    orphan = User(
        email=f"orphan_qr_{uuid.uuid4().hex}@t.com",
        password_hash=hash_password("x"),
        role="employee",
        company_id=company.id,
    )
    session.add(orphan)
    await session.flush()

    sid = await create_session(fake_redis_client, orphan.id)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        cookies={"session_id": str(sid)},
    ) as client:
        r = await client.post("/api/qr/scan", json={"token": token})

    assert r.status_code == HTTPStatus.NOT_FOUND
