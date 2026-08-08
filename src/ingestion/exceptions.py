"""Custom exception hierarchy for RAG document ingestion pipeline."""


class IngestionError(Exception):
    """Base exception for all ingestion pipeline errors."""

    pass


class DocumentLoadError(IngestionError):
    """Exception raised when loading or parsing a source document fails."""

    pass


class CleanError(IngestionError):
    """Exception raised when text cleaning or normalization encounters an error."""

    pass


class ChunkError(IngestionError):
    """Exception raised during document text chunking operations."""

    pass


class AuditError(IngestionError):
    """Exception raised when quality audit checks or thresholds fail."""

    pass
