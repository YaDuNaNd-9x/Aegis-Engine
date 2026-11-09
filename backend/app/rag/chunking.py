import re


def clean_text(text: str) -> str:
    """Normalize extracted document text."""

    text = text.replace("\x00", "")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _looks_like_heading(line: str) -> bool:
    """
    Detect common numbered and uppercase document headings.
    """

    line = line.strip()

    if not line or len(line) > 120:
        return False

    if re.match(
        r"^(chapter|section|part)\s+[\w.-]+",
        line,
        re.IGNORECASE,
    ):
        return True

    if re.match(r"^\d+(\.\d+)*\.?\s+\S+", line):
        return True

    letters = [character for character in line if character.isalpha()]

    if letters:
        uppercase_ratio = sum(
            character.isupper() for character in letters
        ) / len(letters)

        if uppercase_ratio > 0.85 and len(line.split()) <= 12:
            return True

    return False


def _split_into_sections(text: str, default_section: str | None):
    """
    Split page text into logical sections using recognizable headings.
    """

    sections = []
    current_section = default_section
    current_lines = []

    for line in text.splitlines():
        stripped = line.strip()

        if _looks_like_heading(stripped):
            if current_lines:
                sections.append((
                    current_section,
                    "\n".join(current_lines).strip(),
                ))
                current_lines = []

            current_section = stripped
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((
            current_section,
            "\n".join(current_lines).strip(),
        ))

    return [
        (section, content)
        for section, content in sections
        if content
    ]


def _split_text(
    text: str,
    chunk_size: int,
    overlap: int,
) -> list[str]:
    """Split text into overlapping chunks with sensible boundaries."""

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            boundary_candidates = [
                text.rfind(". ", start, end),
                text.rfind("\n", start, end),
                text.rfind(" ", start, end),
            ]

            boundary = max(boundary_candidates)

            if boundary > start + chunk_size // 2:
                end = boundary + 1

        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(chunk_text)

        if end >= len(text):
            break

        start = max(start + 1, end - overlap)

    return chunks


def chunk_document(
    pages: list[dict],
    filename: str,
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[dict]:
    """
    Generate overlapping chunks while retaining source, page,
    section and table metadata.
    """

    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk size or overlap.")

    chunks = []
    chunk_index = 0

    for page_data in pages:
        text = clean_text(page_data.get("text", ""))

        if not text:
            continue

        page_number = page_data.get("page")
        default_section = page_data.get("section")
        table = page_data.get("table")
        table_row = page_data.get("table_row")

        sections = _split_into_sections(
            text,
            default_section,
        )

        for section, section_text in sections:
            text_chunks = _split_text(
                section_text,
                chunk_size,
                overlap,
            )

            for chunk_text in text_chunks:
                chunk_index += 1

                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source": filename,
                        "page": page_number,
                        "section": section or "",
                        "table": table,
                        "table_row": table_row,
                        "chunk_index": chunk_index,
                    },
                })

    return chunks