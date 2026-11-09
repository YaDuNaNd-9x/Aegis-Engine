import re
from pathlib import Path


ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
}

ALLOWED_DATA_EXTENSIONS = {
    ".csv",
}

MAX_FILENAME_LENGTH = 255
MAX_PROMPT_LENGTH = 10000
MAX_INSTRUCTION_LENGTH = 3000


class ValidationError(ValueError):
    """Raised when user input or an uploaded file is invalid."""


def validate_filename(filename: str) -> str:
    """
    Validate and normalize an uploaded filename.
    """

    if not isinstance(filename, str) or not filename.strip():
        raise ValidationError("A valid filename is required.")

    filename = filename.strip()

    if len(filename) > MAX_FILENAME_LENGTH:
        raise ValidationError("Filename is too long.")

    if "\x00" in filename:
        raise ValidationError("Filename contains invalid characters.")

    # Never trust directory information supplied by the client.
    filename = Path(filename.replace("\\", "/")).name

    if filename in {"", ".", ".."}:
        raise ValidationError("Invalid filename.")

    if not re.fullmatch(r"[\w .()\-]+", filename, flags=re.UNICODE):
        raise ValidationError("Filename contains unsupported characters.")

    return filename


def validate_file_extension(
    filename: str,
    allowed_extensions: set[str],
) -> str:
    filename = validate_filename(filename)

    extension = Path(filename).suffix.lower()

    if extension not in allowed_extensions:
        raise ValidationError(
            f"Unsupported file type: {extension or 'unknown'}"
        )

    return filename


def validate_file_content(
    file_bytes: bytes,
    max_bytes: int,
) -> bytes:
    """
    Validate the size and basic presence of uploaded file content.
    """

    if not isinstance(file_bytes, bytes):
        raise ValidationError("Invalid file content.")

    if not file_bytes:
        raise ValidationError("Uploaded file is empty.")

    if len(file_bytes) > max_bytes:
        raise ValidationError("Uploaded file exceeds the size limit.")

    return file_bytes


def validate_prompt(
    prompt: str,
    max_length: int = MAX_PROMPT_LENGTH,
) -> str:
    if not isinstance(prompt, str):
        raise ValidationError("Input must be text.")

    prompt = prompt.strip()

    if not prompt:
        raise ValidationError("Input cannot be empty.")

    if len(prompt) > max_length:
        raise ValidationError("Input exceeds the permitted length.")

    if "\x00" in prompt:
        raise ValidationError("Input contains invalid characters.")

    return prompt


def validate_instruction(instruction: str) -> str:
    instruction = validate_prompt(
        instruction,
        max_length=MAX_INSTRUCTION_LENGTH,
    )

    if len(instruction) < 5:
        raise ValidationError(
            "Instruction must contain at least 5 characters."
        )

    return instruction