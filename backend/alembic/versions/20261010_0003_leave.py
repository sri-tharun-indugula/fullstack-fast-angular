"""leave types balances requests

Revision ID: 20261010_0003
Revises: 20261010_0002
Create Date: 2026-10-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261010_0003"
down_revision: str | Sequence[str] | None = "20261010_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

leave_status = postgresql.ENUM("pending", "approved", "rejected", "cancelled", name="leave_status", create_type=False)


def upgrade() -> None:
    leave_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "leave_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("annual_quota", sa.Numeric(5, 1), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.create_index("ix_leave_types_code", "leave_types", ["code"], unique=True)

    op.create_table(
        "leave_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("leave_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("entitled", sa.Numeric(5, 1), nullable=False),
        sa.Column("used", sa.Numeric(5, 1), nullable=False, server_default="0"),
        sa.Column("pending", sa.Numeric(5, 1), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["leave_type_id"], ["leave_types.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "leave_type_id", "year", name="uq_leave_balance_user_type_year"),
    )
    op.create_index("ix_leave_balances_user_id", "leave_balances", ["user_id"])
    op.create_index("ix_leave_balances_leave_type_id", "leave_balances", ["leave_type_id"])

    op.create_table(
        "leave_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("leave_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("days", sa.Numeric(5, 1), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", leave_status, nullable=False),
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["leave_type_id"], ["leave_types.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_leave_requests_user_id", "leave_requests", ["user_id"])
    op.create_index("ix_leave_requests_leave_type_id", "leave_requests", ["leave_type_id"])


def downgrade() -> None:
    op.drop_index("ix_leave_requests_leave_type_id", table_name="leave_requests")
    op.drop_index("ix_leave_requests_user_id", table_name="leave_requests")
    op.drop_table("leave_requests")
    op.drop_index("ix_leave_balances_leave_type_id", table_name="leave_balances")
    op.drop_index("ix_leave_balances_user_id", table_name="leave_balances")
    op.drop_table("leave_balances")
    op.drop_index("ix_leave_types_code", table_name="leave_types")
    op.drop_table("leave_types")
    leave_status.drop(op.get_bind(), checkfirst=True)
