import io

import pymupdf
import pytesseract

from PIL import Image, ImageOps, ImageEnhance


def _run_ocr(page) -> str:
    """
    Render a PDF page and extract text using Tesseract OCR.
    """

    pixmap = page.get_pixmap(
        matrix=pymupdf.Matrix(2, 2),
        alpha=False,
    )

    image = Image.open(
        io.BytesIO(pixmap.tobytes("png"))
    ).convert("RGB")

    # Basic preprocessing improves OCR readability.
    image = ImageOps.grayscale(image)
    image = ImageEnhance.Contrast(image).enhance(1.5)

    return pytesseract.image_to_string(
        image,
        config="--oem 3 --psm 3",
    ).strip()


def extract_pdf_text_with_ocr(file_bytes: bytes) -> list[dict]:
    """
    Extract text page by page.

    1. Attempt native PDF text extraction.
    2. Apply OCR when a page has insufficient native text.
    3. Preserve page numbers and extraction method.
    """

    if not file_bytes:
        raise ValueError("PDF file is empty.")

    try:
        document = pymupdf.open(
            stream=file_bytes,
            filetype="pdf",
        )
    except Exception as exc:
        raise ValueError(
            f"Unable to open PDF: {exc}"
        ) from exc

    results = []

    try:
        if document.is_encrypted:
            raise ValueError(
                "Encrypted PDFs are not supported."
            )

        if document.page_count == 0:
            raise ValueError("PDF contains no pages.")

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            extraction_method = "native"

            # Use OCR for scanned pages or pages with almost no text.
            if len(text) < 30:
                try:
                    ocr_text = _run_ocr(page)

                    if len(ocr_text) > len(text):
                        text = ocr_text
                        extraction_method = "ocr"

                except Exception as exc:
                    if not text:
                        raise RuntimeError(
                            f"OCR failed on PDF page {page_number}: {exc}"
                        ) from exc

                    extraction_method = "native_fallback"

            if text.strip():
                results.append({
                    "text": text,
                    "page": page_number,
                    "section": None,
                    "extraction_method": extraction_method,
                })

    finally:
        document.close()

    return results