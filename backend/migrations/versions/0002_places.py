"""Searchable places: bus stops and stations, for the From/To suggestions.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-23
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Trigram matching makes search typo-tolerant ("kashmiri gt" finds Kashmere Gate).
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        CREATE TABLE places (
            id          text PRIMARY KEY,           -- source-prefixed, e.g. 'bus:dtc:1449'
            name        text NOT NULL,
            kind        text NOT NULL CHECK (kind IN ('bus_stop', 'metro_station', 'rail_station')),
            detail      text,                       -- e.g. network or stop codes
            search_name text NOT NULL,              -- lower-cased, punctuation removed
            location    geography(Point, 4326) NOT NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX places_search_name_trgm ON places USING gin (search_name gin_trgm_ops)"
    )
    op.execute("CREATE INDEX places_location ON places USING gist (location)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS places")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
