"""add inn/bik to company, currency to schedule

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "company",
        sa.Column("inn", sa.String(12), nullable=True),
    )
    op.add_column(
        "company",
        sa.Column("bik", sa.String(9), nullable=True),
    )

    op.add_column(
        "schedule",
        sa.Column("currency", sa.String(3), nullable=True),
    )
    op.execute(
        """
        UPDATE schedule s
        SET currency = ep.currency
        FROM employee_profile ep
        WHERE s.employee_id = ep.id AND s.currency IS NULL
        """
    )
    op.execute("UPDATE schedule SET currency = 'RUB' WHERE currency IS NULL")
    op.alter_column("schedule", "currency", nullable=False)


def downgrade() -> None:
    op.drop_column("schedule", "currency")
    op.drop_column("company", "bik")
    op.drop_column("company", "inn")
