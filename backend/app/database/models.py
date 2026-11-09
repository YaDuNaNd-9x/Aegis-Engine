from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    event_type = Column(String(100), nullable=False, index=True)
    action = Column(String(255), nullable=False)

    actor = Column(String(100), nullable=True, default="local_user")

    resource_type = Column(String(100), nullable=True)
    resource_name = Column(String(255), nullable=True)

    status = Column(String(50), nullable=False, default="success")
    details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Hash-chain integrity fields.
    previous_hash = Column(String(64), nullable=True)
    record_hash = Column(String(64), nullable=True)


class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id = Column(Integer, primary_key=True, index=True)

    report_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)

    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)

    source_dataset = Column(String(255), nullable=True)

    status = Column(String(50), nullable=False, default="completed")
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)