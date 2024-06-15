"""
This module contains utility functions for managing the PostgreSQL database.
It uses an .env file to determine the target database. 
"""

import os
import shutil  # type: ignore
import argparse  # type: ignore
import asyncpg  # type: ignore
import logging

from sys import exit  # type: ignore
from pathlib import Path  # type: ignore
from contextlib import asynccontextmanager, suppress  # type: ignore

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

with suppress(ImportError):
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv())
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ("DB_PORT")


logger = logging.getLogger(__name__)

logger.info(
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


async def database_exists(conn, db_name):
    row = await conn.fetchrow("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
    return row is not None


async def create_database(conn, db_name, extensions=False):
    if await database_exists(conn, db_name):
        logger.info("Database already exists.")

    await conn.execute(f"CREATE DATABASE {db_name}")
    if extensions:
        await enable_extensions(conn)

    # if await database_exists(conn, db_name):
    #     logger.info("Database created successfully")


async def enable_extensions(conn):
    await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    await conn.close()
    logger.info(f"Extension enabled successfully in database {DB_NAME}.")


async def delete_database(conn, db_name, force=False):
    if force:
        await conn.execute(f"DROP DATABASE {db_name} WITH (FORCE)")
    else:
        await conn.execute(f"DROP DATABASE {db_name}")
    if not await database_exists(conn, db_name):
        logger.info("Database deleted successfully.")
    else:
        logger.info("Failed to delete database")
        exit(1)


# Migration utils
# ---------------
MIGRATIONS_DIR = os.environ.get("MIGRATIONS_DIR")

if (ALEMBIC_INI := os.environ.get("ALEMBIC_INI")) is not None:
    alembic_ini = Path(ALEMBIC_INI)
    if not alembic_ini.exists():
        raise FileNotFoundError(f"alembic.ini not found at {alembic_ini}")
else:
    _p = Path(__file__).parent
    while not (_p / "alembic.ini").exists():
        _p = _p.parent
        if _p == Path("/"):
            raise FileNotFoundError("alembic.ini not found")
    alembic_ini = _p / "alembic.ini"

alembic_cfg = Config(alembic_ini)


async def run_migrations_on_db(database_name):
    def run_upgrade(connection, cfg):
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")

    # db_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{database_name}"
    db_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{database_name}"
    logger.info(f"Running migrations on database {db_url}")

    async_engine = create_async_engine(db_url)
    async with async_engine.begin() as conn:
        await conn.run_sync(run_upgrade, alembic_cfg)


def get_latest_migration() -> str:
    script = ScriptDirectory.from_config(alembic_cfg)
    revision = script.get_current_head()
    if revision is None:
        raise ValueError("No migrations found")
    return revision


def delete_migrations():
    if not MIGRATIONS_DIR:
        logger.info("MIGRATIONS_DIR environment variable not found")
        exit(1)

    migrations_path = Path(MIGRATIONS_DIR)
    if not migrations_path.exists():
        logger.info(f"Migrations directory does not exist at {MIGRATIONS_DIR}")
        exit(1)

    with suppress(FileNotFoundError):
        shutil.rmtree(migrations_path)
    migrations_path.mkdir()


async def check_current_head(database_name):
    # (config.Config, engine.Engine) -> bool
    # db_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{database_name}"
    db_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{database_name}"
    logger.info(f"Checking current head for database {db_url}")

    async_engine = create_async_engine(db_url)
    version = get_latest_migration()
    logger.info(f"Current local migration version: {version}")

    def get_db_version(connection, cfg):
        cfg.attributes["connection"] = connection
        context = MigrationContext.configure(connection)
        return context.get_current_revision()

    async with async_engine.begin() as conn:
        db_version = await conn.run_sync(get_db_version, alembic_cfg)

    logger.info(f"Current db migration version: {db_version}")
    return version == db_version


# Template Database
# -----------------
@asynccontextmanager
async def get_conn(db_name=None):
    try:
        conn = await asyncpg.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=db_name)
        yield conn
    finally:
        await conn.close()


async def delete_template_db(conn):
    db_name = "template_db"
    if await database_exists(conn, db_name):
        logger.info("Deleting existing template_db")
        await conn.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'template_db';")

        await conn.execute(
            "UPDATE pg_database SET datistemplate = FALSE WHERE datname = $1",
            db_name,
        )

        await delete_database(conn, db_name, force=True)


async def load_fixtures(db: AsyncSession):
    await db.commit()


async def create_db_from_template(conn, db_name):
    """Create a new database instance using the template database."""
    template_db_name = "template_db"

    # Check if the database with the given name already exists
    if await database_exists(conn, db_name):
        logger.info(f"Database {db_name} already exists.")
        exit(1)

    # Check if the template database exists
    if not await database_exists(conn, template_db_name):
        logger.error(f"Template database {template_db_name} does not exist.")
        return

    # Terminate all existing connections to template_db
    await conn.execute(
        f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{template_db_name}'
          AND pid <> pg_backend_pid();
    """
    )

    # Create a new database using the template database
    await conn.execute(f"CREATE DATABASE {db_name} WITH TEMPLATE {template_db_name}")
    logger.info(
        f"Database {db_name} created successfully from template {template_db_name}.")


async def main():
    parser = argparse.ArgumentParser(description="Create (or delete) the database.")
    parser.add_argument("--test", action="store_true", help="Use the test database")
    parser.add_argument("--delete", action="store_true",
                        help="Delete the database if it exists.")
    parser.add_argument(
        "--enable-extensions",
        action="store_true",
        help="Enable extensions defined in enable_extensions function body in existing database",
    )
    parser.add_argument(
        "--delete-migrations",
        action="store_true",
        help="Enable extensions defined in enable_extensions function body in existing database",
    )
    parser.add_argument("--recreate", action="store_true",
                        help="Recreate the database (drop and create).")
    parser.add_argument("--create-template", action="store_true",
                        help="Create a template database from migrations.")
    parser.add_argument("--check-current-head", action="store_true",
                        help="Check if the database is up to date.")

    subparsers = parser.add_subparsers(dest="subcommand")
    template_parser = subparsers.add_parser(
        "template", help="Create a template database from migrations.")
    template_parser.add_argument(
        "--create", action="store_true", help="Create the template database.")
    template_parser.add_argument(
        "--delete", action="store_true", help="Delete the template database.")

    args = parser.parse_args()

    if args.subcommand == "template":
        db_name = "template_db"
        if args.create:
            async with get_conn() as conn:
                await create_database(conn, "template_db")
            async with get_conn(db_name="template_db") as conn:
                await enable_extensions(conn)
            await run_migrations_on_db("template_db")

            # db_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/template_db"
            db_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/template_db"
            engine = create_async_engine(db_url, echo="debug")
            Session = async_sessionmaker(engine, expire_on_commit=False)
            async with Session() as db:
                await load_fixtures(db)

            async with get_conn() as conn:
                await conn.execute("ALTER DATABASE template_db WITH CONNECTION LIMIT 0")
                await conn.execute("REVOKE CONNECT ON DATABASE template_db FROM PUBLIC")

                # Make it a template database
                await conn.execute(
                    "UPDATE pg_database SET datistemplate = TRUE WHERE datname = $1",
                    db_name,
                )
            exit(0)
        elif args.delete:
            async with get_conn() as conn:
                await delete_template_db(conn)
            exit(0)
        else:
            logger.info("No action specified.")
            exit(1)

    db_name = os.environ["DB_NAME_TEST"] if args.test else DB_NAME
    # DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"
    DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"
    logger.info(f"DB_URL: {DB_URL}")

    engine = create_async_engine(DB_URL)
    conn = await asyncpg.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=db_name, port=DB_PORT)
    try:
        db_exists = await database_exists(conn, db_name)

        if args.recreate:
            if db_exists:
                await delete_database(conn, db_name)
            await create_database(conn, db_name)
        elif args.delete:
            if db_exists:
                await delete_database(conn, db_name)
            else:
                logger.info("Database does not exist.")
                exit(1)
        elif args.enable_extensions:
            if db_exists:
                await enable_extensions(conn)
            else:
                logger.info("Database does not exist.")
                exit(1)
        elif args.delete_migrations:
            delete_migrations()
        elif args.check_current_head:
            await check_current_head(db_name)
        elif db_exists:
            logger.info("Database already exists.")
            exit(1)
        else:
            await create_database(conn, db_name)
    finally:
        await conn.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
