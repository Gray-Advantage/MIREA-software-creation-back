"""rename_contact_phone_to_contact_name

Revision ID: c8609b939a33
Revises: 259d14a84ad4
Create Date: 2026-02-19 21:03:17.106880

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c8609b939a33'
down_revision: Union[str, None] = '259d14a84ad4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('company', 'contact_phone', new_column_name='contact_name', type_=sa.String(255))


def downgrade() -> None:
    op.alter_column('company', 'contact_name', new_column_name='contact_phone', type_=sa.String(20))
