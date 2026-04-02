"""create user_book_baseline table

Revision ID: 0001_create_user_book_baseline
Revises: 
Create Date: 2026-03-31
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_user_book_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'user_book_baseline' not in inspector.get_table_names():
        op.create_table(
            'user_book_baseline',
            sa.Column('id', sa.Integer, primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer, sa.ForeignKey(
                'user.id'), nullable=False, index=True),
            sa.Column('book_version', sa.String(
                length=255), nullable=False, index=True),
            sa.Column('baseline_page', sa.Integer,
                      nullable=False, server_default='0'),
            sa.Column('baseline_chapter', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False,
                      server_default=sa.text('now()')),
        )

    uq_names = {
        c.get('name') for c in inspector.get_unique_constraints('user_book_baseline')
    }
    uq_relation_exists = bind.execute(
        sa.text("SELECT 1 FROM pg_class WHERE relname = :name LIMIT 1"),
        {"name": "uq_user_book_baseline"},
    ).scalar() is not None

    if 'uq_user_book_baseline' not in uq_names and not uq_relation_exists:
        op.create_unique_constraint(
            'uq_user_book_baseline',
            'user_book_baseline',
            ['user_id', 'book_version'],
        )


def downgrade() -> None:
    op.drop_table('user_book_baseline')
