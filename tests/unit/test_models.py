"""Unit tests for immutable Pydantic V2 domain models."""

import pytest
from pydantic import ValidationError

from ingestion.models import (
    AuditReport,
    BaseDomainModel,
    Chunk,
    Document,
    DocumentReport,
    IngestionConfig,
    IngestionMetrics,
    IngestionReport,
    LoadedDocument,
    StrategyType,
)


def test_base_domain_model_immutability_and_extra_forbid() -> None:
    """Verify BaseDomainModel enforces frozen state and forbids extra attributes."""

    class SampleModel(BaseDomainModel):
        name: str

    model = SampleModel(name="test")
    assert model.name == "test"

    with pytest.raises(ValidationError):
        model.name = "changed"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        SampleModel(name="test", unexpected_field=123)  # type: ignore[call-arg]


def test_strategy_type_enum() -> None:
    """Verify StrategyType enum values and string compatibility."""
    assert StrategyType.FIXED == "fixed"
    assert StrategyType.RECURSIVE == "recursive"
    assert StrategyType("fixed") == StrategyType.FIXED
    assert StrategyType("recursive") == StrategyType.RECURSIVE


def test_ingestion_config_defaults_and_validation() -> None:
    """Verify IngestionConfig default values and bounds validation."""
    config = IngestionConfig()
    assert config.strategy == StrategyType.RECURSIVE
    assert config.chunk_size == 512
    assert config.overlap == 64
    assert config.min_chunk_size == 50
    assert config.coverage_threshold == 0.98

    with pytest.raises(ValidationError):
        IngestionConfig(chunk_size=0)

    with pytest.raises(ValidationError):
        IngestionConfig(coverage_threshold=1.5)

    with pytest.raises(ValidationError):
        config.chunk_size = 1024  # type: ignore[misc]


def test_loaded_document_and_alias() -> None:
    """Verify LoadedDocument model properties, alias identity, and immutability."""
    assert Document is LoadedDocument

    doc = LoadedDocument(
        id="doc_001",
        file_path="/tmp/test.md",
        content="Hello world this is a test document.",
        metadata={"author": "Alice"},
    )
    assert doc.id == "doc_001"
    assert doc.char_count == 36
    assert doc.token_count == 7
    assert doc.metadata["author"] == "Alice"

    with pytest.raises(ValidationError):
        doc.content = "New content"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        LoadedDocument(id="d1", file_path="p", content="c", extra_attr="invalid")  # type: ignore[call-arg]


def test_chunk_model_properties_and_immutability() -> None:
    """Verify Chunk model attributes, document_id alias, and immutability."""
    chunk = Chunk(
        id="chk_001",
        doc_id="doc_001",
        chunk_index=0,
        content="Hello world",
        start_char=0,
        end_char=11,
        token_count=2,
    )
    assert chunk.id == "chk_001"
    assert chunk.doc_id == "doc_001"
    assert chunk.document_id == "doc_001"
    assert chunk.is_orphan_block is False

    with pytest.raises(ValidationError):
        chunk.content = "Modified"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        Chunk(
            id="c",
            doc_id="d",
            chunk_index=0,
            content="x",
            start_char=0,
            end_char=1,
            token_count=1,
            unknown_prop=True,  # type: ignore[call-arg]
        )


def test_document_report_model() -> None:
    """Verify DocumentReport initialization, default values, and immutability."""
    report = DocumentReport(
        document_id="doc_001",
        source_path="data/doc1.md",
    )
    assert report.document_id == "doc_001"
    assert report.char_coverage_ratio == 1.0
    assert report.status == "ok"
    assert report.errors == []

    with pytest.raises(ValidationError):
        report.status = "error"  # type: ignore[misc]


def test_ingestion_report_model() -> None:
    """Verify IngestionReport model timestamp auto-generation and immutability."""
    doc_report = DocumentReport(document_id="d1", source_path="p1")
    report = IngestionReport(
        corpus_path="data/input",
        strategy_used="recursive",
        documents=[doc_report],
        total_chunks=5,
    )
    assert report.corpus_path == "data/input"
    assert len(report.documents) == 1
    assert report.has_blocking_alerts is False
    assert report.execution_timestamp is not None

    with pytest.raises(ValidationError):
        report.total_chunks = 10  # type: ignore[misc]


def test_audit_report_and_metrics_immutability() -> None:
    """Verify legacy IngestionMetrics and AuditReport models enforce immutability."""
    metrics = IngestionMetrics(
        total_docs=1,
        total_chunks=2,
        total_original_chars=100,
        total_chunk_chars=100,
        char_coverage_ratio=1.0,
        duplicate_char_ratio=0.0,
        orphan_block_count=0,
        status="PASSED",
    )
    audit = AuditReport(
        timestamp="2026-08-08T12:00:00Z",
        strategy_used="fixed",
        metrics=metrics,
    )
    assert audit.metrics.total_docs == 1

    with pytest.raises(ValidationError):
        metrics.status = "FAILED"  # type: ignore[misc]
