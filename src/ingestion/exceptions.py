"""Custom exception hierarchy for RAG document ingestion pipeline."""

from typing import Any


class IngestionError(Exception):
    """Base exception for all document ingestion pipeline errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception context to dictionary representation."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class DocumentLoadError(IngestionError):
    """Raised when loading or parsing a source document fails."""

    pass


class CleanError(IngestionError):
    """Raised when text cleaning or normalization encounters an error."""

    pass


class ChunkError(IngestionError):
    """Raised during document text chunking operations."""

    pass


class AuditError(IngestionError):
    """Raised when quality audit checks or thresholds fail."""

    pass

