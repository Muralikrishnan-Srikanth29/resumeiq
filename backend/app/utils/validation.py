import hashlib

import bleach

from app.core.config import get_settings
from app.core.exceptions import (
    FileTooLargeError,
    TextTooLongError,
    TextTooShortError,
)


def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sanitize_text(text: str) -> str:
    """Strip any HTML/script content from pasted text — defends against
    stored-XSS if this text is ever rendered back without escaping."""
    return bleach.clean(text, tags=[], attributes={}, strip=True).strip()


def validate_resume_text(text: str) -> str:
    settings = get_settings()
    cleaned = sanitize_text(text)
    if len(cleaned) < settings.MIN_RESUME_TEXT_CHARS:
        raise TextTooShortError(
            f"Resume text must be at least {settings.MIN_RESUME_TEXT_CHARS} characters."
        )
    if len(cleaned) > settings.MAX_RESUME_TEXT_CHARS:
        raise TextTooLongError(f"Resume text exceeds {settings.MAX_RESUME_TEXT_CHARS} characters.")
    return cleaned


def validate_jd_text(text: str) -> str:
    settings = get_settings()
    cleaned = sanitize_text(text)
    if len(cleaned) > settings.MAX_JD_TEXT_CHARS:
        raise TextTooLongError(f"Job description exceeds {settings.MAX_JD_TEXT_CHARS} characters.")
    return cleaned


def validate_file_size(size_bytes: int) -> None:
    settings = get_settings()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise FileTooLargeError(f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit.")
