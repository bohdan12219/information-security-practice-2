"""add audit_log

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-12 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('http_method', sa.String(length=10), nullable=True),
        sa.Column('endpoint', sa.String(length=200), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('audit_log') as batch:
        batch.create_index('ix_audit_action_ts', ['action', 'timestamp'])
        batch.create_index('ix_audit_ip_action', ['ip_address', 'action'])
        batch.create_index('ix_audit_user_ts', ['user_id', 'timestamp'])
        batch.create_index('ix_audit_log_timestamp', ['timestamp'])

def downgrade() -> None:
    op.drop_table('audit_log')