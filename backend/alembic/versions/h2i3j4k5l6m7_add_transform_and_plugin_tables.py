"""add transform settings, plugin preferences, and audit_logs tables

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-05-31

global_transform_settings, user_transform_settings, user_plugin_preferences,
and audit_logs were defined in models but never had migrations created for them.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h2i3j4k5l6m7"
down_revision: Union[str, Sequence[str], None] = "g1h2i3j4k5l6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=False),
        sa.Column("resource_id", sa.String(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_project_id", "audit_logs", ["project_id"])

    op.create_table(
        "global_transform_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("transform_name", sa.String(), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transform_name"),
    )
    op.create_index(
        "ix_global_transform_settings_transform_name",
        "global_transform_settings",
        ["transform_name"],
    )

    op.create_table(
        "user_transform_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("transform_name", sa.String(), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_transform_settings_user_id",
        "user_transform_settings",
        ["user_id"],
    )
    op.create_index(
        "ix_user_transform_settings_transform_name",
        "user_transform_settings",
        ["transform_name"],
    )

    op.create_table(
        "user_plugin_preferences",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("plugin_name", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "plugin_name"),
    )


def downgrade() -> None:
    op.drop_table("user_plugin_preferences")
    op.drop_index(
        "ix_user_transform_settings_transform_name",
        table_name="user_transform_settings",
    )
    op.drop_index(
        "ix_user_transform_settings_user_id",
        table_name="user_transform_settings",
    )
    op.drop_table("user_transform_settings")
    op.drop_index(
        "ix_global_transform_settings_transform_name",
        table_name="global_transform_settings",
    )
    op.drop_table("global_transform_settings")
    op.drop_index("ix_audit_logs_project_id", table_name="audit_logs")
    op.drop_table("audit_logs")
