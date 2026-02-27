"""add employee phone

Revision ID: d3e8f1a2b4c5
Revises: c8609b939a33
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d3e8f1a2b4c5"
down_revision: Union[str, None] = "c8609b939a33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employee_profile",
        sa.Column("phone", sa.String(length=30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("employee_profile", "phone")
