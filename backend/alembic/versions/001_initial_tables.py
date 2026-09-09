"""Initial tables creation for CropHealthAI

Revision ID: 001_initial_tables
Revises: 
Create Date: 2026-09-09 13:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('role', sa.String(length=50), server_default='farmer', nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('preferred_language', sa.String(length=50), server_default='en', nullable=False),
        sa.Column('points', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_points', 'users', ['points'], unique=False)

    # 2. reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('crop_type', sa.String(length=100), nullable=False),
        sa.Column('image_path', sa.String(length=500), nullable=True),
        sa.Column('location_lat', sa.Float(), nullable=True),
        sa.Column('location_lng', sa.Float(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reports_id', 'reports', ['id'], unique=False)
    op.create_index('ix_reports_submitted_at', 'reports', ['submitted_at'], unique=False)

    # 3. disease_predictions table
    op.create_table(
        'disease_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=True),
        sa.Column('disease_name', sa.String(length=150), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('overlay_path', sa.String(length=500), nullable=True),
        sa.Column('explanation_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_disease_predictions_id', 'disease_predictions', ['id'], unique=False)
    op.create_index('ix_disease_predictions_disease_name', 'disease_predictions', ['disease_name'], unique=False)

    # 4. reward_points table
    op.create_table(
        'reward_points',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reward_points_id', 'reward_points', ['id'], unique=False)

    # 5. community_trends table
    op.create_table(
        'community_trends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('disease_name', sa.String(length=150), nullable=False),
        sa.Column('location_geojson', sa.JSON(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_community_trends_id', 'community_trends', ['id'], unique=False)
    op.create_index('ix_community_trends_disease_name', 'community_trends', ['disease_name'], unique=False)
    op.create_index('ix_community_trends_location', 'community_trends', ['location'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_community_trends_location', table_name='community_trends')
    op.drop_index('ix_community_trends_disease_name', table_name='community_trends')
    op.drop_index('ix_community_trends_id', table_name='community_trends')
    op.drop_table('community_trends')

    op.drop_index('ix_reward_points_id', table_name='reward_points')
    op.drop_table('reward_points')

    op.drop_index('ix_disease_predictions_disease_name', table_name='disease_predictions')
    op.drop_index('ix_disease_predictions_id', table_name='disease_predictions')
    op.drop_table('disease_predictions')

    op.drop_index('ix_reports_submitted_at', table_name='reports')
    op.drop_index('ix_reports_id', table_name='reports')
    op.drop_table('reports')

    op.drop_index('ix_users_points', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')
