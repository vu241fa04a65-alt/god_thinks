import re
import html
import unicodedata
from typing import Optional


# Regex patterns for sanitization
TAG_RE = re.compile(r"<[^>]+>")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
DANGEROUS_PATTERNS = [
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"vbscript:", re.IGNORECASE),
    re.compile(r"data:text/html", re.IGNORECASE),
    re.compile(r"onload=", re.IGNORECASE),
    re.compile(r"onerror=", re.IGNORECASE),
    re.compile(r"onclick=", re.IGNORECASE),
]


def sanitize_text(text: Optional[str], max_length: int = 2000) -> str:
    """
    Sanitize general text input to prevent XSS, script injection, and control character exploits.
    """
    if not text:
        return ""

    # 1. Normalize unicode characters (NFKC)
    cleaned = unicodedata.normalize("NFKC", str(text))

    # 2. Strip null bytes and non-printable control characters
    cleaned = CONTROL_CHAR_RE.sub("", cleaned)

    # 3. Strip HTML markup tags
    cleaned = TAG_RE.sub("", cleaned)

    # 4. Strip dangerous inline event handlers
    for pattern in DANGEROUS_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    # 5. HTML entity escape remaining special characters (&, <, >, ", ')
    cleaned = html.escape(cleaned.strip(), quote=True)

    # 6. Enforce length boundary
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned


def sanitize_filename(filename: Optional[str]) -> str:
    """
    Sanitize uploaded filenames to prevent Directory Traversal (../) and path injection.
    """
    if not filename:
        return "unnamed_file"

    # Remove path traversal characters
    safe = filename.replace("\\", "/").split("/")[-1]
    safe = safe.replace("\x00", "").strip()

    # Normalize unicode
    safe = unicodedata.normalize("NFKC", safe)

    # Keep only safe alphanumeric characters, dashes, underscores, and dots
    safe = re.sub(r"[^\w.\-]", "_", safe)

    # Prevent hidden files starting with .
    safe = safe.lstrip(".")

    # Ensure file has a valid name and extension
    if not safe or safe == ".":
        safe = "upload_file"

    return safe[:100]
