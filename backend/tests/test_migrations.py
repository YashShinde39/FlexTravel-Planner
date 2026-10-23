import asyncio

from alembic import command
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.conftest import alembic_config


def installed_extensions(url: str) -> set[str]:
    async def query() -> set[str]:
        engine = create_async_engine(url)
        try:
            async with engine.connect() as conn:
                return set((await conn.scalars(text("SELECT extname FROM pg_extension"))).all())
        finally:
            await engine.dispose()

    return asyncio.run(query())


def test_migrations_upgrade_and_downgrade_cleanly(empty_database_url: str):
    config = alembic_config(empty_database_url)

    command.upgrade(config, "head")
    assert "postgis" in installed_extensions(empty_database_url)

    command.downgrade(config, "base")
    assert "postgis" not in installed_extensions(empty_database_url)

    # Upgrading again proves the downgrade left the database in a re-migratable state.
    command.upgrade(config, "head")
    assert "postgis" in installed_extensions(empty_database_url)
