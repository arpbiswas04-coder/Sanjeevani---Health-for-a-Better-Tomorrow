from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
import re
from sqlalchemy.engine import make_url

# Append root directory to sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.core.database import Base
from app.core.migration_filters import extension_table_filter
import app.models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    # Sync driver for alembic migrations
    db_url = settings.get_database_url()
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "+psycopg2")
    return db_url.replace("+aiosqlite", "")

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def include_object(obj, name, type_, reflected, compare_to):
    # This PostgreSQL expression index is managed explicitly by the migration.
    # ORM reflection cannot portably compare its geography cast; live tests check it.
    return not (type_ == 'index' and name == 'ix_facilities_geography')


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        hide_parameters=True,
    )

    with connectable.connect() as connection:
        test_schema = os.environ.get('ALEMBIC_TEST_SCHEMA')
        if test_schema:
            if connection.dialect.name != 'postgresql' or not (make_url(get_url()).database or '').endswith('_test') or not re.fullmatch(r'test_[0-9a-f]{32}', test_schema):
                raise RuntimeError('Test migration schema requires a disposable _test database and generated schema name')
            connection.exec_driver_sql(f'SET search_path TO "{test_schema}", public')
            connection.commit()
        include_extension_name = extension_table_filter(connection)
        def include_name(name, type_, parents):
            # With search_path-based test isolation, reflection reports the
            # schema-qualified version table as schema=None. It is Alembic's
            # own bookkeeping, not an unmanaged application table.
            if test_schema and type_ == 'table' and name == 'alembic_version' and parents.get('schema_name') in (None, test_schema):
                return False
            return include_extension_name(name, type_, parents)
        # Catalog reflection starts SQLAlchemy's implicit transaction. Finish
        # that read before Alembic takes ownership of its migration transaction.
        connection.commit()
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True,
            version_table_schema=test_schema or None, include_object=include_object,
            include_name=include_name
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
