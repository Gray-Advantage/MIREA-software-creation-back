"""add schedule table

Revision ID: f7a3b2c1d5e8
Revises: e5f2a1b3c4d6
Create Date: 2026-02-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7a3b2c1d5e8"
down_revision: str | None = "e5f2a1b3c4d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schedule",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employee_profile.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_schedule_employee_date",
        "schedule",
        ["employee_id", "date"],
        unique=True,
    )
    op.create_index(
        "ix_schedule_date",
        "schedule",
        ["date"],
    )


def downgrade() -> None:
    op.drop_index("ix_schedule_date", table_name="schedule")
    op.drop_index("ix_schedule_employee_date", table_name="schedule")
    op.drop_table("schedule")
