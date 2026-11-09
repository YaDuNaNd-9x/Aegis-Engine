
from pathlib import Path

from docx import Document

from backend.app.services.report_service import ReportService


def test_generate_docx_report(tmp_path, monkeypatch):

    monkeypatch.setattr(
        "backend.app.services.report_service.REPORT_DIR",
        tmp_path,
    )

    content = {
        "summary": "Machine analysis completed successfully.",
        "sections": [
            {
                "heading": "Observations",
                "content": [
                    "Temperature exceeded the threshold.",
                    "Vibration readings require inspection.",
                ],
            }
        ],
        "metrics": {
            "Average Temperature": "63.48 °C",
            "Maximum Temperature": "79.1 °C",
        },
        "recommendations": [
            "Inspect abnormal machines.",
            "Continue monitoring equipment.",
        ],
    }

    result = ReportService.generate_docx(
        title="Machine Analysis Report",
        report_type="machine_analysis",
        content=content,
        source_dataset="machine_readings.csv",
    )

    file_path = Path(result["file_path"])

    assert result["status"] == "completed"
    assert result["filename"].endswith(".docx")
    assert file_path.exists()
    assert file_path.stat().st_size > 0


def test_generated_report_contains_expected_content(
    tmp_path,
    monkeypatch,
):

    monkeypatch.setattr(
        "backend.app.services.report_service.REPORT_DIR",
        tmp_path,
    )

    result = ReportService.generate_docx(
        title="Industrial Report",
        report_type="analysis",
        content={
            "summary": "Analysis completed.",
            "sections": [
                {
                    "heading": "Results",
                    "content": "Two abnormal readings were detected.",
                }
            ],
            "metrics": {
                "Abnormal Readings": 2,
            },
            "recommendations": [
                "Inspect the affected machines."
            ],
        },
    )

    document = Document(result["file_path"])

    extracted_text = "\n".join(
        paragraph.text for paragraph in document.paragraphs
    )

    assert "Industrial Report" in extracted_text
    assert "Analysis completed." in extracted_text
    assert "Results" in extracted_text
    assert "Two abnormal readings were detected." in extracted_text
    assert "Inspect the affected machines." in extracted_text


def test_report_without_optional_sections(
    tmp_path,
    monkeypatch,
):

    monkeypatch.setattr(
        "backend.app.services.report_service.REPORT_DIR",
        tmp_path,
    )

    result = ReportService.generate_docx(
        title="Basic Report",
        report_type="general",
        content={},
    )

    assert Path(result["file_path"]).exists()
