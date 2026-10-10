"""audit logs

Revision ID: 20261010_0007
Revises: 20261010_0006
Create Date: 2026-10-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261010_0007"
down_revision: str | Sequence[str] | None = "20261010_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

audit_action = postgresql.ENUM(
    "auth.login_success",
    "auth.login_failed",
    "auth.logout",
    "leave.applied",
    "leave.approved",
    "leave.rejected",
    "goal.created",
    "document.uploaded",
    "document.deleted",
    "employee.created",
    "employee.updated",
    name="audit_action",
    create_type=False,
)


def upgrade() -> None:
    audit_action.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    audit_action.drop(op.get_bind(), checkfirst=True)
