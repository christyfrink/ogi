"""add geocode_cache table

Revision ID: g1h2i3j4k5l6
Revises: b1c2d3e4f5a6
Create Date: 2026-05-31

geocode_cache stores resolved geocoding results so the app doesn't need to
hit an external geocoding API on every location search. Was defined in
models/eventing.py but never had a migration created for it.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "geocode_cache",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("source", sa.String(), nullable=False, server_default="cache"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("query"),
    )
    op.create_index("ix_geocode_cache_query", "geocode_cache", ["query"])


def downgrade() -> None:
    op.drop_index("ix_geocode_cache_query", table_name="geocode_cache")
    op.drop_table("geocode_cache")
