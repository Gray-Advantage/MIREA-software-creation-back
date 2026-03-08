"""add rate snapshot to schedule

Revision ID: a1b2c3d4e5f6
Revises: f7a3b2c1d5e8
Create Date: 2026-03-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f7a3b2c1d5e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "schedule",
        sa.Column(
            "rate_type",
            sa.String(20),
            nullable=True,
        ),
    )
    op.add_column(
        "schedule",
        sa.Column(
            "rate_amount",
            sa.Numeric(10, 2),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE schedule s
        SET rate_type = ep.rate_type,
            rate_amount = ep.rate_amount
        FROM employee_profile ep
        WHERE s.employee_id = ep.id
        """,
    )

    op.alter_column("schedule", "rate_type", nullable=False)
    op.alter_column("schedule", "rate_amount", nullable=False)


def downgrade() -> None:
    op.drop_column("schedule", "rate_amount")
    op.drop_column("schedule", "rate_type")
