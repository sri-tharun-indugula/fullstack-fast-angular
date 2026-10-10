"""attendance days

Revision ID: 20261010_0004
Revises: 20261010_0003
Create Date: 2026-10-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261010_0004"
down_revision: str | Sequence[str] | None = "20261010_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attendance_days",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "work_date", name="uq_attendance_user_work_date"),
    )
    op.create_index("ix_attendance_days_user_id", "attendance_days", ["user_id"])
    op.create_index("ix_attendance_days_work_date", "attendance_days", ["work_date"])


def downgrade() -> None:
    op.drop_index("ix_attendance_days_work_date", table_name="attendance_days")
    op.drop_index("ix_attendance_days_user_id", table_name="attendance_days")
    op.drop_table("attendance_days")
