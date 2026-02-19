from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "company"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    legal_form: Mapped[str] = mapped_column(String(50))
    legal_address: Mapped[str] = mapped_column(Text)
    contact_phone: Mapped[str] = mapped_column(String(20))
    business_area: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    users: Mapped[list["User"]] = relationship(back_populates="company")
    qr_sessions: Mapped[list["QRSession"]] = relationship(back_populates="company")


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    company: Mapped["Company"] = relationship(back_populates="users")
    profile: Mapped[Optional["EmployeeProfile"]] = relationship(back_populates="user")
    sessions: Mapped[list["ApiSession"]] = relationship(back_populates="user")


class EmployeeProfile(Base):
    __tablename__ = "employee_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    patronymic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position: Mapped[str] = mapped_column(String(255))
    rate_type: Mapped[str] = mapped_column(String(20))
    rate_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="profile")
    adjustments: Mapped[list["Adjustment"]] = relationship(back_populates="employee")
    time_entries: Mapped[list["TimeEntry"]] = relationship(back_populates="employee")


class Adjustment(Base):
    __tablename__ = "adjustment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee_profile.id"))
    type: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    comment: Mapped[str] = mapped_column(Text)
    date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    employee: Mapped["EmployeeProfile"] = relationship(back_populates="adjustments")


class QRSession(Base):
    __tablename__ = "qr_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[uuid.UUID] = mapped_column(
        Uuid, unique=True, default=uuid.uuid4
    )
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company: Mapped["Company"] = relationship(back_populates="qr_sessions")


class TimeEntry(Base):
    __tablename__ = "time_entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee_profile.id"))
    date: Mapped[date] = mapped_column(Date)
    check_in: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    check_out: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    employee: Mapped["EmployeeProfile"] = relationship(back_populates="time_entries")


class ApiSession(Base):
    __tablename__ = "api_session"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="sessions")
