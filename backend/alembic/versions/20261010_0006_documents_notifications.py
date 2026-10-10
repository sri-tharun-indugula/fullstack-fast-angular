"""hr documents and notifications

Revision ID: 20261010_0006
Revises: 20261010_0005
Create Date: 2026-10-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261010_0006"
down_revision: str | Sequence[str] | None = "20261010_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

document_scope = postgresql.ENUM("company", "employee", name="document_scope", create_type=False)
notification_kind = postgresql.ENUM(
    "leave_submitted",
    "leave_approved",
    "leave_rejected",
    "goal_assigned",
    "document_available",
    name="notification_kind",
    create_type=False,
)


def upgrade() -> None:
    document_scope.create(op.get_bind(), checkfirst=True)
    notification_kind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "hr_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scope", document_scope, nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("stored_filename", sa.String(length=64), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index("ix_hr_documents_owner_user_id", "hr_documents", ["owner_user_id"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", notification_kind, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_hr_documents_owner_user_id", table_name="hr_documents")
    op.drop_table("hr_documents")
    notification_kind.drop(op.get_bind(), checkfirst=True)
    document_scope.drop(op.get_bind(), checkfirst=True)
