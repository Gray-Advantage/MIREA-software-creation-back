import datetime as _dt
from decimal import Decimal
from http import HTTPStatus
from unittest.mock import ANY

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Adjustment, Company, EmployeeProfile, Schedule, User
from api.services.auth import hash_password
from tests.base import AuthTestView


async def _get_profile(
    session: AsyncSession,
    user_id: int,
) -> EmployeeProfile:
    result = await session.execute(
        select(EmployeeProfile).where(EmployeeProfile.user_id == user_id),
    )
    return result.scalar_one()


class TestFinalSalaryGet(AuthTestView):
    URL = "/api/employees/{employee_id}"
    METHOD = "GET"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client, path={"employee_id": 0})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_no_schedule_no_adjustments(
        self,
        auth_client: AsyncClient,
        employee_user: User,
    ) -> None:
        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
        )

        assert response.json() == {
            "id": employee_user.id,
            "email": "employee@test.com",
            "is_active": True,
            "profile": {
                "id": ANY,
                "user_id": employee_user.id,
                "full_name": "Тестовый Сотрудник",
                "phone": "+79991234567",
                "position": "Разработчик",
                "rate_type": "hourly",
                "rate_amount": "500.00",
                "currency": "RUB",
                "avatar_url": None,
                "created_at": ANY,
                "updated_at": None,
                "schedule": [],
            },
            "monthly_salary": "0.00",
            "final_salary": "0.00",
        }

    async def test_schedule_only__hourly(
        self,
        auth_client: AsyncClient,
        employee_user: User,
        session: AsyncSession,
    ) -> None:
        profile = await _get_profile(session, employee_user.id)
        today = _dt.datetime.now(_dt.UTC).date()

        session.add(
            Schedule(
                employee_id=profile.id,
                date=today,
                start_time=_dt.time(9, 0),
                end_time=_dt.time(18, 0),
                rate_type="hourly",
                rate_amount=Decimal("500.00"),
                currency="RUB",
            ),
        )
        await session.flush()

        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            params={"month": today.strftime("%Y-%m")},
        )

        assert response.json() == {
            "id": employee_user.id,
            "email": "employee@test.com",
            "is_active": True,
            "profile": ANY,
            "monthly_salary": "4500.00",
            "final_salary": "4500.00",
        }

    async def test_with_bonus(
        self,
        auth_client: AsyncClient,
        employee_user: User,
        session: AsyncSession,
    ) -> None:
        profile = await _get_profile(session, employee_user.id)
        today = _dt.datetime.now(_dt.UTC).date()

        session.add(
            Schedule(
                employee_id=profile.id,
                date=today,
                start_time=_dt.time(9, 0),
                end_time=_dt.time(18, 0),
                rate_type="hourly",
                rate_amount=Decimal("500.00"),
                currency="RUB",
            ),
        )
        session.add(
            Adjustment(
                employee_id=profile.id,
                type="bonus",
                amount=Decimal("1000.00"),
                comment="Премия за месяц",
                date=today,
            ),
        )
        await session.flush()

        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            params={"month": today.strftime("%Y-%m")},
        )

        # 9h * 500 = 4500, + bonus 1000 = 5500
        assert response.json() == {
            "id": employee_user.id,
            "email": "employee@test.com",
            "is_active": True,
            "profile": ANY,
            "monthly_salary": "4500.00",
            "final_salary": "5500.00",
        }

    async def test_with_fine(
        self,
        auth_client: AsyncClient,
        employee_user: User,
        session: AsyncSession,
    ) -> None:
        profile = await _get_profile(session, employee_user.id)
        today = _dt.datetime.now(_dt.UTC).date()

        session.add(
            Schedule(
                employee_id=profile.id,
                date=today,
                start_time=_dt.time(9, 0),
                end_time=_dt.time(18, 0),
                rate_type="hourly",
                rate_amount=Decimal("500.00"),
                currency="RUB",
            ),
        )
        session.add(
            Adjustment(
                employee_id=profile.id,
                type="fine",
                amount=Decimal("500.00"),
                comment="Штраф за опоздание",
                date=today,
            ),
        )
        await session.flush()

        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            params={"month": today.strftime("%Y-%m")},
        )

        # 9h * 500 = 4500, - fine 500 = 4000
        assert response.json() == {
            "id": employee_user.id,
            "email": "employee@test.com",
            "is_active": True,
            "profile": ANY,
            "monthly_salary": "4500.00",
            "final_salary": "4000.00",
        }

    async def test_with_bonus_and_fine(
        self,
        auth_client: AsyncClient,
        employee_user: User,
        session: AsyncSession,
    ) -> None:
        profile = await _get_profile(session, employee_user.id)
        today = _dt.datetime.now(_dt.UTC).date()

        for day_offset in range(2):
            session.add(
                Schedule(
                    employee_id=profile.id,
                    date=today + _dt.timedelta(days=day_offset),
                    start_time=_dt.time(10, 0),
                    end_time=_dt.time(18, 0),
                    rate_type="hourly",
                    rate_amount=Decimal("500.00"),
                    currency="RUB",
                ),
            )
        session.add(
            Adjustment(
                employee_id=profile.id,
                type="bonus",
                amount=Decimal("2000.00"),
                comment="Премия",
                date=today,
            ),
        )
        session.add(
            Adjustment(
                employee_id=profile.id,
                type="fine",
                amount=Decimal("300.00"),
                comment="Штраф",
                date=today,
            ),
        )
        await session.flush()

        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            params={"month": today.strftime("%Y-%m")},
        )

        # 2 * 8h * 500 = 8000, + 2000 - 300 = 9700
        assert response.json() == {
            "id": employee_user.id,
            "email": "employee@test.com",
            "is_active": True,
            "profile": ANY,
            "monthly_salary": "8000.00",
            "final_salary": "9700.00",
        }

    async def test_adjustments_other_month_ignored(
        self,
        auth_client: AsyncClient,
        employee_user: User,
        session: AsyncSession,
    ) -> None:
        profile = await _get_profile(session, employee_user.id)
        today = _dt.datetime.now(_dt.UTC).date()
        other_month = today.replace(day=1) + _dt.timedelta(days=60)

        session.add(
            Schedule(
                employee_id=profile.id,
                date=today,
                start_time=_dt.time(9, 0),
                end_time=_dt.time(17, 0),
                rate_type="hourly",
                rate_amount=Decimal("500.00"),
                currency="RUB",
            ),
        )
        session.add(
            Adjustment(
                employee_id=profile.id,
                type="bonus",
                amount=Decimal("5000.00"),
                comment="Премия за другой месяц",
                date=other_month,
            ),
        )
        await session.flush()

        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            params={"month": today.strftime("%Y-%m")},
        )

        # 8h * 500 = 4000, bonus in another month → ignored
        assert response.json() == {
            "id": employee_user.id,
            "email": "employee@test.com",
            "is_active": True,
            "profile": ANY,
            "monthly_salary": "4000.00",
            "final_salary": "4000.00",
        }


class TestFinalSalaryShiftRate(AuthTestView):
    """final_salary для ставки за смену (shift/daily)."""

    URL = "/api/employees/{employee_id}"
    METHOD = "GET"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client, path={"employee_id": 0})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_shift_rate_with_adjustments(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        company: Company,
    ) -> None:
        user = User(
            email="shift_worker@test.com",
            password_hash=hash_password("pass123"),
            role="employee",
            company_id=company.id,
        )
        session.add(user)
        await session.flush()

        profile = EmployeeProfile(
            user_id=user.id,
            full_name="Сменщик Тестовый",
            position="Кассир",
            rate_type="shift",
            rate_amount=Decimal("2000.00"),
            currency="RUB",
        )
        session.add(profile)
        await session.flush()

        today = _dt.datetime.now(_dt.UTC).date()

        for day_offset in range(3):
            session.add(
                Schedule(
                    employee_id=profile.id,
                    date=today + _dt.timedelta(days=day_offset),
                    start_time=_dt.time(8, 0),
                    end_time=_dt.time(20, 0),
                    rate_type="shift",
                    rate_amount=Decimal("2000.00"),
                    currency="RUB",
                ),
            )
        session.add(
            Adjustment(
                employee_id=profile.id,
                type="bonus",
                amount=Decimal("500.00"),
                comment="Бонус",
                date=today,
            ),
        )
        session.add(
            Adjustment(
                employee_id=profile.id,
                type="fine",
                amount=Decimal("200.00"),
                comment="Штраф",
                date=today,
            ),
        )
        await session.flush()

        response = await self.request(
            auth_client,
            path={"employee_id": user.id},
            params={"month": today.strftime("%Y-%m")},
        )

        # 3 shifts * 2000 = 6000, + 500 - 200 = 6300
        assert response.json() == {
            "id": user.id,
            "email": "shift_worker@test.com",
            "is_active": True,
            "profile": ANY,
            "monthly_salary": "6000.00",
            "final_salary": "6300.00",
        }


class TestFinalSalaryList(AuthTestView):
    """final_salary через GET /api/employees (список)."""

    URL = "/api/employees"
    METHOD = "GET"

    async def test_list_includes_final_salary(
        self,
        auth_client: AsyncClient,
        employee_user: User,
        session: AsyncSession,
    ) -> None:
        profile = await _get_profile(session, employee_user.id)
        today = _dt.datetime.now(_dt.UTC).date()

        session.add(
            Schedule(
                employee_id=profile.id,
                date=today,
                start_time=_dt.time(9, 0),
                end_time=_dt.time(18, 0),
                rate_type="hourly",
                rate_amount=Decimal("500.00"),
                currency="RUB",
            ),
        )
        session.add(
            Adjustment(
                employee_id=profile.id,
                type="bonus",
                amount=Decimal("750.00"),
                comment="Премия",
                date=today,
            ),
        )
        await session.flush()

        response = await self.request(
            auth_client,
            params={"month": today.strftime("%Y-%m")},
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) == 1
        # 9h * 500 = 4500, + 750 = 5250
        assert data[0] == {
            "id": employee_user.id,
            "email": "employee@test.com",
            "is_active": True,
            "profile": ANY,
            "monthly_salary": "4500.00",
            "final_salary": "5250.00",
        }


class TestMidMonthRateChange(AuthTestView):
    """Смена ставки посреди месяца — старые записи хранят старую ставку."""

    URL = "/api/employees/{employee_id}"
    METHOD = "GET"

    async def test_error__when_unauthorized(self, client: AsyncClient) -> None:
        response = await self.request(client, path={"employee_id": 0})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_mixed_rates_hourly(
        self,
        auth_client: AsyncClient,
        employee_user: User,
        session: AsyncSession,
    ) -> None:
        """3 дня по 500₽/ч + 3 дня по 700₽/ч (9ч каждый)."""
        profile = await _get_profile(session, employee_user.id)
        today = _dt.datetime.now(_dt.UTC).date()

        for i in range(3):
            session.add(
                Schedule(
                    employee_id=profile.id,
                    date=today + _dt.timedelta(days=i),
                    start_time=_dt.time(9, 0),
                    end_time=_dt.time(18, 0),
                    rate_type="hourly",
                    rate_amount=Decimal("500.00"),
                    currency="RUB",
                ),
            )
        for i in range(3, 6):
            session.add(
                Schedule(
                    employee_id=profile.id,
                    date=today + _dt.timedelta(days=i),
                    start_time=_dt.time(9, 0),
                    end_time=_dt.time(18, 0),
                    rate_type="hourly",
                    rate_amount=Decimal("700.00"),
                    currency="RUB",
                ),
            )
        await session.flush()

        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            params={"month": today.strftime("%Y-%m")},
        )

        # 3 * 9h * 500 + 3 * 9h * 700 = 13500 + 18900 = 32400
        assert response.json() == {
            "id": employee_user.id,
            "email": "employee@test.com",
            "is_active": True,
            "profile": ANY,
            "monthly_salary": "32400.00",
            "final_salary": "32400.00",
        }

    async def test_mixed_rates_shift(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        company: Company,
    ) -> None:
        """2 смены по 2000₽ + 3 смены по 2500₽."""
        user = User(
            email="shift_mixed@test.com",
            password_hash=hash_password("pass123"),
            role="employee",
            company_id=company.id,
        )
        session.add(user)
        await session.flush()

        profile = EmployeeProfile(
            user_id=user.id,
            full_name="Сменщик Микс",
            position="Кассир",
            rate_type="shift",
            rate_amount=Decimal("2500.00"),
            currency="RUB",
        )
        session.add(profile)
        await session.flush()

        today = _dt.datetime.now(_dt.UTC).date()

        for i in range(2):
            session.add(
                Schedule(
                    employee_id=profile.id,
                    date=today + _dt.timedelta(days=i),
                    start_time=_dt.time(8, 0),
                    end_time=_dt.time(20, 0),
                    rate_type="shift",
                    rate_amount=Decimal("2000.00"),
                    currency="RUB",
                ),
            )
        for i in range(2, 5):
            session.add(
                Schedule(
                    employee_id=profile.id,
                    date=today + _dt.timedelta(days=i),
                    start_time=_dt.time(8, 0),
                    end_time=_dt.time(20, 0),
                    rate_type="shift",
                    rate_amount=Decimal("2500.00"),
                    currency="RUB",
                ),
            )
        await session.flush()

        response = await self.request(
            auth_client,
            path={"employee_id": user.id},
            params={"month": today.strftime("%Y-%m")},
        )

        # 2 * 2000 + 3 * 2500 = 4000 + 7500 = 11500
        assert response.json() == {
            "id": user.id,
            "email": "shift_mixed@test.com",
            "is_active": True,
            "profile": ANY,
            "monthly_salary": "11500.00",
            "final_salary": "11500.00",
        }

    async def test_rate_change_via_api_keeps_old_entries(
        self,
        auth_client: AsyncClient,
        employee_user: User,
        session: AsyncSession,
    ) -> None:
        """Изменяем ставку через PATCH без замены расписания —
        старые записи сохраняют прежнюю ставку."""
        profile = await _get_profile(session, employee_user.id)
        today = _dt.datetime.now(_dt.UTC).date()

        for i in range(3):
            session.add(
                Schedule(
                    employee_id=profile.id,
                    date=today + _dt.timedelta(days=i),
                    start_time=_dt.time(9, 0),
                    end_time=_dt.time(18, 0),
                    rate_type="hourly",
                    rate_amount=Decimal("500.00"),
                    currency="RUB",
                ),
            )
        await session.flush()

        await auth_client.patch(
            f"/api/employees/{employee_user.id}",
            json={"rate_amount": "800.00"},
        )

        response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            params={"month": today.strftime("%Y-%m")},
        )

        data = response.json()
        assert data["profile"]["rate_amount"] == "800.00"
        # 3 * 9h * 500 (old rate on entries) = 13500
        assert data["monthly_salary"] == "13500.00"

    async def test_rate_change_with_new_schedule_uses_new_rate(
        self,
        auth_client: AsyncClient,
        employee_user: User,
        session: AsyncSession,
    ) -> None:
        """Изменяем ставку + замена расписания — новые записи
        получают новую ставку."""
        today = _dt.datetime.now(_dt.UTC).date()

        response = await auth_client.patch(
            f"/api/employees/{employee_user.id}",
            json={
                "rate_amount": "800.00",
                "schedule": [
                    {
                        "date": str(today + _dt.timedelta(days=i)),
                        "start_time": "09:00:00",
                        "end_time": "18:00:00",
                    }
                    for i in range(3)
                ],
            },
        )
        assert response.status_code == HTTPStatus.OK

        get_response = await self.request(
            auth_client,
            path={"employee_id": employee_user.id},
            params={"month": today.strftime("%Y-%m")},
        )

        # 3 * 9h * 800 (new rate) = 21600
        assert get_response.json() == {
            "id": employee_user.id,
            "email": "employee@test.com",
            "is_active": True,
            "profile": ANY,
            "monthly_salary": "21600.00",
            "final_salary": "21600.00",
        }
