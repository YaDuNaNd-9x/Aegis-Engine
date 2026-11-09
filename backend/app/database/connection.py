from pathlib import Path

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from backend.app.database.models import Base


Path("storage").mkdir(parents=True, exist_ok=True)

DATABASE_URL = "sqlite+aiosqlite:///./storage/aegis.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def _migrate_audit_columns(connection):
    """Add hash-chain columns to an existing SQLite audit table."""

    def migrate(sync_connection):
        inspector = inspect(sync_connection)

        if "audit_logs" not in inspector.get_table_names():
            return

        columns = {
            column["name"]
            for column in inspector.get_columns("audit_logs")
        }

        if "previous_hash" not in columns:
            sync_connection.execute(
                text(
                    "ALTER TABLE audit_logs "
                    "ADD COLUMN previous_hash VARCHAR(64)"
                )
            )

        if "record_hash" not in columns:
            sync_connection.execute(
                text(
                    "ALTER TABLE audit_logs "
                    "ADD COLUMN record_hash VARCHAR(64)"
                )
            )

    await connection.run_sync(migrate)


async def init_db():
    """Create tables and apply compatible schema migrations."""

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await _migrate_audit_columns(connection)

    # Backfill pre-existing audit rows once, if none have been chained.
    from backend.app.services.audit_service import AuditService

    async with AsyncSessionLocal() as session:
        await AuditService.backfill_legacy_chain(session)


async def get_db():
    """Provide an asynchronous database session."""

    async with AsyncSessionLocal() as session:
        yield session


async def check_db_connection():
    """Verify database connectivity."""

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    return True


async def close_db():
    """Dispose of the database engine."""

    await engine.dispose()