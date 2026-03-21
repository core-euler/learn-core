"""add slugs for course sync

Revision ID: 2f5c3d8a1b67
Revises: c7a9d1f4b2e0
Create Date: 2026-03-21 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f5c3d8a1b67'
down_revision: Union[str, Sequence[str], None] = 'c7a9d1f4b2e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('modules') as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=255), nullable=True))
        batch_op.create_index(batch_op.f('ix_modules_slug'), ['slug'], unique=True)

    with op.batch_alter_table('lessons') as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=255), nullable=True))
        batch_op.create_index(batch_op.f('ix_lessons_slug'), ['slug'], unique=False)
        batch_op.create_unique_constraint('uq_lessons_module_slug', ['module_id', 'slug'])


def downgrade() -> None:
    with op.batch_alter_table('lessons') as batch_op:
        batch_op.drop_constraint('uq_lessons_module_slug', type_='unique')
        batch_op.drop_index(batch_op.f('ix_lessons_slug'))
        batch_op.drop_column('slug')

    with op.batch_alter_table('modules') as batch_op:
        batch_op.drop_index(batch_op.f('ix_modules_slug'))
        batch_op.drop_column('slug')
