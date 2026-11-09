import asyncio
import hashlib
import json

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.models import AuditLog


GENESIS_HASH = "0" * 64

# Serializes writes within this application process.
_audit_write_lock = asyncio.Lock()


class AuditService:

    @staticmethod
    def _canonical_payload(log: AuditLog) -> str:
        """Serialize an audit record deterministically for hashing."""

        payload = {
            "id": log.id,
            "event_type": log.event_type,
            "action": log.action,
            "actor": log.actor,
            "resource_type": log.resource_type,
            "resource_name": log.resource_name,
            "status": log.status,
            "details": log.details,
            "error_message": log.error_message,
            "created_at": (
                log.created_at.isoformat()
                if log.created_at
                else None
            ),
            "previous_hash": log.previous_hash,
        }

        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )

    @staticmethod
    def _calculate_hash(log: AuditLog) -> str:
        payload = AuditService._canonical_payload(log)

        return hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()

    @staticmethod
    async def log_event(
        db: AsyncSession,
        event_type: str,
        action: str,
        actor: str = "local_user",
        resource_type: Optional[str] = None,
        resource_name: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ):
        """Create and persist a hash-chained audit event."""

        async with _audit_write_lock:
            try:
                result = await db.execute(
                    select(AuditLog)
                    .order_by(desc(AuditLog.id))
                    .limit(1)
                )
                previous_record = result.scalars().first()

                previous_hash = (
                    previous_record.record_hash
                    if previous_record and previous_record.record_hash
                    else GENESIS_HASH
                )

                if previous_record and not previous_record.record_hash:
                    raise RuntimeError(
                        "Cannot append to an audit chain with an unchained record. "
                        "Run the database migration and verify the chain first."
                    )

                log = AuditLog(
                    event_type=event_type,
                    action=action,
                    actor=actor,
                    resource_type=resource_type,
                    resource_name=resource_name,
                    status=status,
                    details=details,
                    error_message=error_message,
                    created_at=datetime.utcnow(),
                    previous_hash=previous_hash,
                )

                db.add(log)

                # The database assigns the ID during flush.
                await db.flush()

                log.record_hash = AuditService._calculate_hash(log)

                await db.commit()
                await db.refresh(log)

                return log

            except Exception:
                await db.rollback()
                raise

    @staticmethod
    async def backfill_legacy_chain(db: AsyncSession) -> int:
        """
        Chain existing records if the entire audit table is unchained.

        This is intended for the one-time migration from the old schema.
        A partially chained table is not silently rewritten.
        """

        result = await db.execute(
            select(AuditLog).order_by(AuditLog.id.asc())
        )
        logs = result.scalars().all()

        if not logs:
            return 0

        if any(log.record_hash for log in logs):
            return 0

        previous_hash = GENESIS_HASH

        try:
            for log in logs:
                log.previous_hash = previous_hash
                log.record_hash = AuditService._calculate_hash(log)
                previous_hash = log.record_hash

            await db.commit()
            return len(logs)

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        limit: int = 100,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
    ):
        """Retrieve audit logs with optional filters."""

        query = select(AuditLog)

        if event_type:
            query = query.where(AuditLog.event_type == event_type)

        if status:
            query = query.where(AuditLog.status == status)

        query = query.order_by(desc(AuditLog.id)).limit(limit)

        result = await db.execute(query)

        return result.scalars().all()

    @staticmethod
    async def get_log_count(db: AsyncSession) -> int:
        """Return the total number of audit records."""

        result = await db.execute(
            select(func.count(AuditLog.id))
        )

        return result.scalar_one()

    @staticmethod
    async def verify_chain(db: AsyncSession) -> Dict[str, Any]:
        """Verify record hashes and links in chronological order."""

        result = await db.execute(
            select(AuditLog).order_by(AuditLog.id.asc())
        )
        logs = result.scalars().all()

        if not logs:
            return {
                "valid": True,
                "total_records": 0,
                "verified_records": 0,
                "first_invalid_record_id": None,
                "message": "Audit chain is empty.",
            }

        previous_hash = GENESIS_HASH
        verified_count = 0

        for log in logs:
            if not log.previous_hash or not log.record_hash:
                return {
                    "valid": False,
                    "total_records": len(logs),
                    "verified_records": verified_count,
                    "first_invalid_record_id": log.id,
                    "message": "An audit record is missing its hash fields.",
                }

            if log.previous_hash != previous_hash:
                return {
                    "valid": False,
                    "total_records": len(logs),
                    "verified_records": verified_count,
                    "first_invalid_record_id": log.id,
                    "message": "Previous-hash link mismatch detected.",
                }

            expected_hash = AuditService._calculate_hash(log)

            if expected_hash != log.record_hash:
                return {
                    "valid": False,
                    "total_records": len(logs),
                    "verified_records": verified_count,
                    "first_invalid_record_id": log.id,
                    "message": "Record content or hash has been modified.",
                }

            verified_count += 1
            previous_hash = log.record_hash

        return {
            "valid": True,
            "total_records": len(logs),
            "verified_records": len(logs),
            "first_invalid_record_id": None,
            "message": "All audit records passed hash-chain verification.",
        }