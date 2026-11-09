from pathlib import Path
import io
import re

from docx import Document

from backend.app.rag.ocr import extract_pdf_text_with_ocr


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _extract_docx(file_bytes: bytes) -> list[dict]:
    document = Document(io.BytesIO(file_bytes))
    results = []
    current_section = None

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if not text:
            continue

        style_name = getattr(paragraph.style, "name", "") or ""

        if "heading" in style_name.lower() or style_name.lower() == "title":
            current_section = text

        results.append({
            "text": text,
            "page": None,
            "section": current_section,
        })

    for table_index, table in enumerate(document.tables, start=1):
        for row_index, row in enumerate(table.rows, start=1):
            row_text = " | ".join(
                cell.text.strip().replace("\n", " ")
                for cell in row.cells
            )

            if row_text.strip():
                results.append({
                    "text": row_text,
                    "page": None,
                    "section": current_section,
                    "table": table_index,
                    "table_row": row_index,
                })

    return results


def extract_document(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Extract readable text from PDF, DOCX and TXT files.

    PDF extraction preserves page numbers.
    DOCX extraction preserves headings and table information.
    """

    if not file_bytes:
        raise ValueError("Uploaded document is empty.")

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported document format: {extension}"
        )

    try:
        if extension == ".pdf":
            results = extract_pdf_text_with_ocr(file_bytes)

        elif extension == ".docx":
            results = _extract_docx(file_bytes)

        else:
            text = file_bytes.decode("utf-8-sig", errors="replace").strip()

            results = [{
                "text": text,
                "page": None,
                "section": None,
            }] if text else []

    except ValueError:
        raise

    except Exception as exc:
        raise ValueError(
            f"Could not extract content from {filename}: {exc}"
        ) from exc

    results = [
        item for item in results
        if item.get("text", "").strip()
    ]

    if not results:
        raise ValueError(
            "No readable text found in the uploaded document. "
            "The file may be empty, encrypted, or image-only."
        )

    return results