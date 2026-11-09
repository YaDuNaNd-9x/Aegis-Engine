import re
from typing import Optional


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
    r"ignore\s+your\s+(safety\s+)?rules",
    r"reveal\s+(the\s+)?(system\s+)?prompt",
    r"reveal\s+(all\s+)?secrets",
    r"you\s+are\s+now\s+an\s+unrestricted",
    r"bypass\s+(all\s+)?safety",
    r"override\s+(all\s+)?instructions",
    r"execute\s+this\s+command",
    r"act\s+as\s+(an?\s+)?(unrestricted|unauthorized)",
    r"developer\s+mode\s+(enabled|activated)",
    r"ignore\s+the\s+system\s+message",
    r"print\s+(all\s+)?environment\s+variables",
    r"exfiltrate\s+(the\s+)?(data|secrets|credentials)",
    r"send\s+(the\s+)?(data|files|secrets)\s+to",
    r"reveal\s+(the\s+)?api\s+key",
    r"show\s+(me\s+)?your\s+hidden\s+instructions",
]

COMPILED_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in INJECTION_PATTERNS
]


def sanitize_prompt(prompt: str) -> str:
    """
    Normalize incoming text without changing its meaning.
    """

    if not isinstance(prompt, str):
        raise TypeError("Prompt must be a string.")

    prompt = prompt.replace("\x00", "")
    prompt = prompt.replace("\r\n", "\n")
    prompt = prompt.replace("\r", "\n")

    prompt = re.sub(r"[ \t]+", " ", prompt)

    return prompt.strip()


def check_prompt_injection(prompt: str) -> Optional[str]:
    """
    Detect common prompt-injection patterns.

    This is a heuristic detector, not a complete defense
    against prompt injection.
    """

    if not isinstance(prompt, str) or not prompt.strip():
        return None

    normalized = sanitize_prompt(prompt)

    for pattern in COMPILED_PATTERNS:
        if pattern.search(normalized):
            return "Potential prompt injection detected."

    return None


def inspect_document_content(content: str) -> dict:
    """
    Inspect untrusted document text for common injection patterns.

    Documents are not automatically rejected because legitimate
    documents may discuss prompt injection as a subject.
    """

    warning = check_prompt_injection(content)

    return {
        "suspicious": warning is not None,
        "warning": warning,
        "treat_as_untrusted": True,
    }


def validate_user_prompt(prompt: str) -> str:
    """
    Sanitize and reject user prompts matching known injection patterns.
    """

    sanitized = sanitize_prompt(prompt)

    if not sanitized:
        raise ValueError("Prompt cannot be empty.")

    warning = check_prompt_injection(sanitized)

    if warning:
        raise ValueError(warning)

    return sanitized