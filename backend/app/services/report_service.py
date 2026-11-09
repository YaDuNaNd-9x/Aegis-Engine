import re
import uuid

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.models import GeneratedReport


REPORT_DIR = Path("storage/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


class ReportService:

    @staticmethod
    def _safe_filename(title: str) -> str:
        safe_title = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            title.strip(),
        ).strip("_")

        return safe_title[:100] or "Aegis_Report"

    @staticmethod
    def _add_bullet_list(document: Document, items):
        for item in items:
            document.add_paragraph(str(item), style="List Bullet")

    @staticmethod
    def generate_docx(
        title: str,
        report_type: str,
        content: Dict[str, Any],
        source_dataset: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a structured DOCX report from supplied content."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        unique_id = uuid.uuid4().hex[:8]

        filename = (
            f"{ReportService._safe_filename(title)}_"
            f"{timestamp}_{unique_id}.docx"
        )

        file_path = REPORT_DIR / filename
        temporary_path = REPORT_DIR / f".{filename}.tmp"

        document = Document()

        section = document.sections[0]
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

        heading = document.add_heading(title, level=0)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

        document.add_paragraph(f"Report Type: {report_type}")
        document.add_paragraph(
            f"Generated On: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
        )

        if source_dataset:
            document.add_paragraph(
                f"Source Dataset: {source_dataset}"
            )

        document.add_paragraph(
            "Prepared by Aegis Engine from the information supplied "
            "for this report."
        )

        document.add_paragraph("")

        # Executive summary
        summary = content.get("summary")

        if summary:
            document.add_heading("Executive Summary", level=1)
            document.add_paragraph(str(summary))

        # Main sections
        sections = content.get("sections", [])

        if sections:
            document.add_heading("Analysis and Findings", level=1)

        for section_data in sections:
            if not isinstance(section_data, dict):
                continue

            section_title = str(
                section_data.get("heading", "Section")
            )
            section_content = section_data.get("content", "")

            document.add_heading(section_title, level=2)

            if isinstance(section_content, list):
                ReportService._add_bullet_list(
                    document,
                    section_content,
                )
            else:
                document.add_paragraph(str(section_content))

        # Metrics
        metrics = content.get("metrics", {})

        if metrics and isinstance(metrics, dict):
            document.add_heading("Key Metrics", level=1)

            table = document.add_table(rows=1, cols=2)
            table.style = "Light Grid Accent 1"

            header = table.rows[0].cells
            header[0].text = "Metric"
            header[1].text = "Value"

            for key, value in metrics.items():
                cells = table.add_row().cells
                cells[0].text = str(key)
                cells[1].text = str(value)

        # Evidence
        evidence = content.get("evidence", [])

        if evidence:
            document.add_heading("Evidence", level=1)

            for index, item in enumerate(evidence, start=1):
                if not isinstance(item, dict):
                    document.add_paragraph(str(item))
                    continue

                document.add_heading(
                    f"Evidence Item {index}",
                    level=2,
                )

                for field, label in (
                    ("finding", "Finding"),
                    ("source", "Source"),
                    ("page", "Page"),
                    ("section", "Section"),
                    ("quote", "Supporting Extract"),
                    ("citation", "Citation"),
                ):
                    value = item.get(field)

                    if value is not None and value != "":
                        paragraph = document.add_paragraph()
                        paragraph.add_run(f"{label}: ").bold = True
                        paragraph.add_run(str(value))

        # Citations and sources
        citations = content.get("citations", [])

        if citations:
            document.add_heading("Sources and Citations", level=1)

            for citation in citations:
                if isinstance(citation, dict):
                    parts = [
                        f"{key}: {value}"
                        for key, value in citation.items()
                        if value is not None and value != ""
                    ]
                    document.add_paragraph(
                        "; ".join(parts),
                        style="List Number",
                    )
                else:
                    document.add_paragraph(
                        str(citation),
                        style="List Number",
                    )

        # Recommendations
        recommendations = content.get("recommendations", [])

        if recommendations:
            document.add_heading("Recommendations", level=1)
            ReportService._add_bullet_list(
                document,
                recommendations,
            )

        # Report limitations / evidence note
        document.add_heading("Report Notes", level=1)
        document.add_paragraph(
            "This report presents the supplied analysis, evidence, "
            "metrics, and references. Conclusions should be checked "
            "against the original operational records and applicable "
            "industrial procedures before being used for decisions."
        )

        # Footer
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer.add_run(
            "Generated by Aegis Engine | Local Industrial AI Workbench"
        ).font.size = Pt(9)

        try:
            document.save(temporary_path)
            temporary_path.replace(file_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        return {
            "filename": filename,
            "file_path": str(file_path),
            "title": title,
            "report_type": report_type,
            "status": "completed",
        }

    @staticmethod
    async def save_report_record(
        db: AsyncSession,
        report_data: Dict[str, Any],
        source_dataset: Optional[str] = None,
        summary: Optional[str] = None,
    ):
        """Save generated report metadata in the database."""

        report = GeneratedReport(
            report_type=report_data["report_type"],
            title=report_data["title"],
            filename=report_data["filename"],
            file_path=report_data["file_path"],
            source_dataset=source_dataset,
            status="completed",
            summary=summary,
            completed_at=datetime.utcnow(),
        )

        try:
            db.add(report)
            await db.commit()
            await db.refresh(report)
            return report
        except Exception:
            await db.rollback()
            Path(report_data["file_path"]).unlink(missing_ok=True)
            raise

    @staticmethod
    async def get_reports(
        db: AsyncSession,
        limit: int = 100,
    ):
        """Retrieve generated report history."""

        result = await db.execute(
            select(GeneratedReport)
            .order_by(desc(GeneratedReport.created_at))
            .limit(limit)
        )

        return result.scalars().all()

    @staticmethod
    async def get_report_by_id(
        db: AsyncSession,
        report_id: int,
    ):
        result = await db.execute(
            select(GeneratedReport).where(
                GeneratedReport.id == report_id
            )
        )

        return result.scalar_one_or_none()