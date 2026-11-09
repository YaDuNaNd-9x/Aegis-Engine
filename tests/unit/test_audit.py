
import pytest

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from backend.app.database.models import Base
from backend.app.services.audit_service import AuditService


@pytest.fixture
async def db_session(tmp_path):

    database_path = tmp_path / "test_audit.db"

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_path}",
        echo=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_audit_event(db_session):

    log = await AuditService.log_event(
        db=db_session,
        event_type="analysis",
        action="CSV analysis completed",
        resource_type="dataset",
        resource_name="machine_readings.csv",
        status="success",
        details={"rows": 16},
    )

    assert log.id is not None
    assert log.event_type == "analysis"
    assert log.status == "success"
    assert log.resource_name == "machine_readings.csv"


@pytest.mark.asyncio
async def test_retrieve_audit_logs(db_session):

    await AuditService.log_event(
        db=db_session,
        event_type="report",
        action="Report generated",
    )

    logs = await AuditService.get_logs(
        db=db_session,
        limit=10,
    )

    assert len(logs) == 1
    assert logs[0].event_type == "report"


@pytest.mark.asyncio
async def test_filter_audit_logs_by_event_type(db_session):

    await AuditService.log_event(
        db=db_session,
        event_type="report",
        action="Report generated",
    )

    await AuditService.log_event(
        db=db_session,
        event_type="analysis",
        action="CSV analyzed",
    )

    logs = await AuditService.get_logs(
        db=db_session,
        event_type="analysis",
    )

    assert len(logs) == 1
    assert logs[0].event_type == "analysis"


@pytest.mark.asyncio
async def test_filter_audit_logs_by_status(db_session):

    await AuditService.log_event(
        db=db_session,
        event_type="analysis",
        action="Analysis completed",
        status="success",
    )

    await AuditService.log_event(
        db=db_session,
        event_type="analysis",
        action="Analysis failed",
        status="failed",
    )

    logs = await AuditService.get_logs(
        db=db_session,
        status="failed",
    )

    assert len(logs) == 1
    assert logs[0].status == "failed"


@pytest.mark.asyncio
async def test_audit_log_count(db_session):

    await AuditService.log_event(
        db=db_session,
        event_type="chat",
        action="Chat request",
    )

    await AuditService.log_event(
        db=db_session,
        event_type="document",
        action="Document uploaded",
    )

    count = await AuditService.get_log_count(db_session)

    assert count == 2
