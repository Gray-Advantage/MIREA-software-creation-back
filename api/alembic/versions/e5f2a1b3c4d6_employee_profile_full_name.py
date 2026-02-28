"""employee_profile: first_name, last_name, patronymic -> full_name

Revision ID: e5f2a1b3c4d6
Revises: d3e8f1a2b4c5
Create Date: 2026-02-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f2a1b3c4d6"
down_revision: str | None = "d3e8f1a2b4c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "employee_profile",
        sa.Column("full_name", sa.String(length=320), nullable=True),
    )
    op.execute(
        """
        UPDATE employee_profile
        SET full_name = trim(
            concat(
                coalesce(last_name, ''),
                ' ',
                coalesce(first_name, ''),
                ' ',
                coalesce(patronymic, '')
            )
        )
        """
    )
    op.alter_column(
        "employee_profile",
        "full_name",
        existing_type=sa.String(length=320),
        nullable=False,
    )
    op.drop_column("employee_profile", "first_name")
    op.drop_column("employee_profile", "last_name")
    op.drop_column("employee_profile", "patronymic")


def downgrade() -> None:
    op.add_column(
        "employee_profile",
        sa.Column("first_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "employee_profile",
        sa.Column("last_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "employee_profile",
        sa.Column("patronymic", sa.String(length=100), nullable=True),
    )
    op.execute(
        """
        UPDATE employee_profile
        SET
            last_name = coalesce(split_part(trim(full_name), ' ', 1), ''),
            first_name = coalesce(nullif(split_part(trim(full_name), ' ', 2), ''), ''),
            patronymic = case
                when array_length(string_to_array(trim(full_name), ' '), 1) > 2
                then trim(substring(
                    trim(full_name)
                    from length(split_part(trim(full_name), ' ', 1))
                    + length(split_part(trim(full_name), ' ', 2)) + 3
                ))
                else null
            end
        """
    )
    op.alter_column(
        "employee_profile",
        "first_name",
        nullable=False,
    )
    op.alter_column(
        "employee_profile",
        "last_name",
        nullable=False,
    )
    op.drop_column("employee_profile", "full_name")
