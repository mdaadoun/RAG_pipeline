"""Unit tests for custom exception hierarchy."""

import pytest
from ingestion.exceptions import (
    AuditError,
    ChunkError,
    CleanError,
    DocumentLoadError,
    IngestionError,
)


def test_ingestion_error_base_properties() -> None:
    """Verify base IngestionError message and default details dictionary."""
    err = IngestionError("Pipeline failure")
    assert str(err) == "Pipeline failure"
    assert err.message == "Pipeline failure"
    assert err.details == {}


def test_ingestion_error_with_details() -> None:
    """Verify IngestionError with custom details dictionary."""
    details = {"file_path": "doc.md", "code": 404}
    err = IngestionError("File missing", details=details)
    assert err.message == "File missing"
    assert err.details == {"file_path": "doc.md", "code": 404}


def test_ingestion_error_to_dict() -> None:
    """Verify exception dictionary serialization format."""
    err = IngestionError("Test error", details={"stage": "loader"})
    serialized = err.to_dict()
    assert serialized == {
        "error_type": "IngestionError",
        "message": "Test error",
        "details": {"stage": "loader"},
    }


def test_derived_exceptions_inheritance() -> None:
    """Verify inheritance hierarchy for derived exception classes."""
    exceptions = [
        DocumentLoadError("Load failed"),
        CleanError("Clean failed"),
        ChunkError("Chunk failed"),
        AuditError("Audit failed"),
    ]
    for err in exceptions:
        assert isinstance(err, IngestionError)
        assert isinstance(err, Exception)


def test_derived_exceptions_polymorphic_catch() -> None:
    """Verify catching derived exceptions using base IngestionError type."""
    try:
        raise DocumentLoadError("Corrupted file", details={"path": "bad.pdf"})
    except IngestionError as exc:
        assert isinstance(exc, DocumentLoadError)
        assert exc.message == "Corrupted file"
        assert exc.details == {"path": "bad.pdf"}
        assert exc.to_dict()["error_type"] == "DocumentLoadError"


def test_all_derived_exceptions_to_dict_type_names() -> None:
    """Verify error_type in to_dict matches exact class names for all derived errors."""
    cases = [
        (DocumentLoadError("err"), "DocumentLoadError"),
        (CleanError("err"), "CleanError"),
        (ChunkError("err"), "ChunkError"),
        (AuditError("err"), "AuditError"),
    ]
    for exc, expected_type in cases:
        assert exc.to_dict()["error_type"] == expected_type
