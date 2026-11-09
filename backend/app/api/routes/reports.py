from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.connection import get_db
from backend.app.services.report_service import ReportService
from backend.app.services.audit_service import AuditService
from backend.app.schemas.reports import ReportRequest
from backend.app.security.permissions import (
    Role,
    require_permission,
    PermissionDenied,
)


router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"],
)


@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
):
    report_data = None

    try:
        require_permission(Role.OPERATOR, "report_generate")

        content = request.content.model_dump()

        report_data = ReportService.generate_docx(
            title=request.title,
            report_type=request.report_type,
            content=content,
            source_dataset=request.source_dataset,
        )

        report = await ReportService.save_report_record(
            db=db,
            report_data=report_data,
            source_dataset=request.source_dataset,
            summary=content.get("summary"),
        )

        await AuditService.log_event(
            db=db,
            event_type="report",
            action="DOCX report generated",
            resource_type="report",
            resource_name=report.filename,
            details={
                "report_id": report.id,
                "report_type": report.report_type,
                "source_dataset": report.source_dataset,
            },
        )

        return {
            "message": "Report generated successfully",
            "report_id": report.id,
            "filename": report.filename,
            "download_url": (
                f"/api/v1/reports/download/{report.id}"
            ),
        }

    except PermissionDenied as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        await db.rollback()

        

        try:
            await AuditService.log_event(
                db=db,
                event_type="report",
                action="DOCX report generation failed",
                status="failed",
                error_message=str(exc),
            )
        except Exception:
            await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(exc)}",
        ) from exc


@router.get("/")
async def list_reports(
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    try:
        require_permission(Role.VIEWER, "report_view")

        reports = await ReportService.get_reports(
            db=db,
            limit=limit,
        )

        return [
            {
                "id": report.id,
                "title": report.title,
                "filename": report.filename,
                "report_type": report.report_type,
                "source_dataset": report.source_dataset,
                "status": report.status,
                "summary": report.summary,
                "created_at": report.created_at,
                "completed_at": report.completed_at,
            }
            for report in reports
        ]

    except PermissionDenied as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc


@router.get("/download/{report_id}")
async def download_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        require_permission(Role.VIEWER, "report_view")

        report = await ReportService.get_report_by_id(
            db=db,
            report_id=report_id,
        )

        if not report:
            raise HTTPException(
                status_code=404,
                detail="Report not found",
            )

        file_path = Path(report.file_path)

        if not file_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="Report file does not exist",
            )

        return FileResponse(
            path=file_path,
            filename=report.filename,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )

    except PermissionDenied as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc