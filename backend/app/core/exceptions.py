"""
Domain exceptions. Mapped to HTTP responses centrally in main.py's
exception handlers rather than scattered try/except in every route.
"""


class ResumeIQError(Exception):
    """Base exception for all domain errors."""
    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class FileValidationError(ResumeIQError):
    status_code = 400
    detail = "Invalid file."


class FileTooLargeError(FileValidationError):
    detail = "File exceeds maximum allowed size."


class UnsupportedFileTypeError(FileValidationError):
    detail = "Unsupported file type. Upload a PDF or DOCX file."


class TextTooShortError(FileValidationError):
    detail = "Resume text is too short to analyze meaningfully."


class TextTooLongError(FileValidationError):
    detail = "Text exceeds maximum allowed length."


class ParsingError(ResumeIQError):
    status_code = 422
    detail = "Could not parse the document. It may be corrupted, scanned-image-only, or empty."


class ResourceNotFoundError(ResumeIQError):
    status_code = 404
    detail = "Resource not found."


class RateLimitExceededError(ResumeIQError):
    status_code = 429
    detail = "Rate limit exceeded. Please try again later."


class AIServiceError(ResumeIQError):
    status_code = 502
    detail = "AI analysis service is temporarily unavailable."


class DatabaseError(ResumeIQError):
    status_code = 503
    detail = "Database operation failed."
