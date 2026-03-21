"""add rag index cache tables

Revision ID: c7a9d1f4b2e0
Revises: 9b8d6b3d2a1c
Create Date: 2026-03-21 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7a9d1f4b2e0'
down_revision: Union[str, Sequence[str], None] = '9b8d6b3d2a1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'rag_chunks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('content_signature', sa.String(length=64), nullable=False),
        sa.Column('chunk_id', sa.String(length=255), nullable=False),
        sa.Column('module_id', sa.String(length=255), nullable=False),
        sa.Column('lesson_id', sa.String(length=255), nullable=False),
        sa.Column('source_path', sa.String(length=1000), nullable=False),
        sa.Column('start_char', sa.Integer(), nullable=False),
        sa.Column('end_char', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('embedding_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rag_chunks_content_signature'), 'rag_chunks', ['content_signature'], unique=False)
    op.create_index(op.f('ix_rag_chunks_chunk_id'), 'rag_chunks', ['chunk_id'], unique=True)
    op.create_index(op.f('ix_rag_chunks_module_id'), 'rag_chunks', ['module_id'], unique=False)
    op.create_index(op.f('ix_rag_chunks_lesson_id'), 'rag_chunks', ['lesson_id'], unique=False)
    op.create_index(op.f('ix_rag_chunks_source_path'), 'rag_chunks', ['source_path'], unique=False)

    op.create_table(
        'rag_index_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_signature', sa.String(length=64), nullable=False),
        sa.Column('embed_model', sa.String(length=255), nullable=False),
        sa.Column('chunk_size_chars', sa.Integer(), nullable=False),
        sa.Column('chunk_overlap_chars', sa.Integer(), nullable=False),
        sa.Column('embeddings_ready', sa.Boolean(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rag_index_state_content_signature'), 'rag_index_state', ['content_signature'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_rag_index_state_content_signature'), table_name='rag_index_state')
    op.drop_table('rag_index_state')

    op.drop_index(op.f('ix_rag_chunks_source_path'), table_name='rag_chunks')
    op.drop_index(op.f('ix_rag_chunks_lesson_id'), table_name='rag_chunks')
    op.drop_index(op.f('ix_rag_chunks_module_id'), table_name='rag_chunks')
    op.drop_index(op.f('ix_rag_chunks_chunk_id'), table_name='rag_chunks')
    op.drop_index(op.f('ix_rag_chunks_content_signature'), table_name='rag_chunks')
    op.drop_table('rag_chunks')
