import asyncio
import os
from collections.abc import Iterator
from pathlib import Path

import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from app.core.config import Settings
from app.main import create_app

# A separate database so tests never touch development data. docker-compose.yml creates it;
# CI provides it as a service container.
TEST_DATABASE_URL = os.environ.get(
    "FLEXTRAVEL_TEST_DATABASE_URL",
    "postgresql+asyncpg://flextravel:flextravel@localhost:5433/flextravel_test",
)
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def alembic_config(url: str) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


@pytest.fixture(scope="session")
def database_url() -> str:
    """The test database, migrated to the latest schema once per test run."""
    command.upgrade(alembic_config(TEST_DATABASE_URL), "head")
    return TEST_DATABASE_URL


def make_client(database_url: str) -> TestClient:
    return TestClient(create_app(Settings(environment="test", database_url=database_url)))


@pytest.fixture
def client(database_url: str) -> Iterator[TestClient]:
    with make_client(database_url) as test_client:
        yield test_client


@pytest.fixture
def empty_database_url() -> Iterator[str]:
    """A brand-new database with no extensions, dropped after the test.

    Created from template0, which never contains extensions, so the result doesn't depend on
    how the server was set up (the PostGIS image pre-installs extensions in its main database).
    """
    url = make_url(TEST_DATABASE_URL)
    name = f"{url.database}_empty"
    admin_dsn = url.set(drivername="postgresql", database="postgres").render_as_string(
        hide_password=False
    )

    async def admin(sql: str) -> None:
        connection = await asyncpg.connect(admin_dsn)
        try:
            await connection.execute(sql)
        finally:
            await connection.close()

    asyncio.run(admin(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    asyncio.run(admin(f'CREATE DATABASE "{name}" TEMPLATE template0'))
    try:
        yield url.set(database=name).render_as_string(hide_password=False)
    finally:
        asyncio.run(admin(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
