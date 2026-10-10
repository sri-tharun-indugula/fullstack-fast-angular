"""departments and employee profiles

Revision ID: 20261010_0002
Revises: 20261010_0001
Create Date: 2026-10-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261010_0002"
down_revision: str | Sequence[str] | None = "20261010_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["departments.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_departments_code", "departments", ["code"], unique=True)
    op.create_index("ix_departments_parent_id", "departments", ["parent_id"])

    op.create_table(
        "employee_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("manager_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employee_code", sa.String(length=32), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("work_location", sa.String(length=255), nullable=True),
        sa.Column("joined_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["manager_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_employee_profiles_user_id", "employee_profiles", ["user_id"], unique=True)
    op.create_index("ix_employee_profiles_employee_code", "employee_profiles", ["employee_code"], unique=True)
    op.create_index("ix_employee_profiles_department_id", "employee_profiles", ["department_id"])
    op.create_index("ix_employee_profiles_manager_user_id", "employee_profiles", ["manager_user_id"])


def downgrade() -> None:
    op.drop_index("ix_employee_profiles_manager_user_id", table_name="employee_profiles")
    op.drop_index("ix_employee_profiles_department_id", table_name="employee_profiles")
    op.drop_index("ix_employee_profiles_employee_code", table_name="employee_profiles")
    op.drop_index("ix_employee_profiles_user_id", table_name="employee_profiles")
    op.drop_table("employee_profiles")
    op.drop_index("ix_departments_parent_id", table_name="departments")
    op.drop_index("ix_departments_code", table_name="departments")
    op.drop_table("departments")
