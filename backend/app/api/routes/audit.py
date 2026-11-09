from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.connection import get_db
from backend.app.services.audit_service import AuditService
from backend.app.security.permissions import (
    Role,
    require_permission,
    PermissionDenied,
)


router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Audit Logs"],
)


@router.get("/")
async def get_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        require_permission(Role.VIEWER, "audit_view")

        logs = await AuditService.get_logs(
            db=db,
            limit=limit,
            event_type=event_type,
            status=status,
        )

        return [
            {
                "id": log.id,
                "event_type": log.event_type,
                "action": log.action,
                "actor": log.actor,
                "resource_type": log.resource_type,
                "resource_name": log.resource_name,
                "status": log.status,
                "details": log.details,
                "error_message": log.error_message,
                "created_at": log.created_at,
                "previous_hash": log.previous_hash,
                "record_hash": log.record_hash,
            }
            for log in logs
        ]

    except PermissionDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/stats")
async def get_audit_stats(
    db: AsyncSession = Depends(get_db),
):
    try:
        require_permission(Role.VIEWER, "audit_view")

        total = await AuditService.get_log_count(db)

        return {
            "total_events": total,
        }

    except PermissionDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/verify")
async def verify_audit_chain(
    db: AsyncSession = Depends(get_db),
):
    try:
        require_permission(Role.VIEWER, "audit_view")

        return await AuditService.verify_chain(db)

    except PermissionDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc