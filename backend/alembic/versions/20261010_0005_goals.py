"""performance goals

Revision ID: 20261010_0005
Revises: 20261010_0004
Create Date: 2026-10-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261010_0005"
down_revision: str | Sequence[str] | None = "20261010_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

goal_status = postgresql.ENUM(
    "not_started",
    "in_progress",
    "completed",
    "cancelled",
    name="goal_status",
    create_type=False,
)


def upgrade() -> None:
    goal_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "performance_goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("assignee_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", goal_status, nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("manager_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_performance_goals_assignee_user_id", "performance_goals", ["assignee_user_id"])


def downgrade() -> None:
    op.drop_index("ix_performance_goals_assignee_user_id", table_name="performance_goals")
    op.drop_table("performance_goals")
    goal_status.drop(op.get_bind(), checkfirst=True)
