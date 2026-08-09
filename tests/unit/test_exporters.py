"""Unit tests for JSONL and Audit Report exporters."""

from pathlib import Path

import pytest

from ingestion.exceptions import AuditError
from ingestion.exporters import (
    AuditReportExporter,
    JSONLChunkExporter,
    export_audit_report,
    export_chunks_jsonl,
)
from ingestion.models import (
    AuditReport,
    Chunk,
    DocumentReport,
    IngestionMetrics,
    IngestionReport,
)


@pytest.fixture
def sample_chunks() -> list[Chunk]:
    """Fixture providing sample Chunk domain model instances."""
    return [
        Chunk(
            id="doc1_0",
            doc_id="doc1",
            chunk_index=0,
            content="Sample text chunk 1 content with special UTF-8 chars: éàç.",
            start_char=0,
            end_char=55,
            token_count=10,
            is_orphan_block=False,
            metadata={"source": "file1.md"},
        ),
        Chunk(
            id="doc1_1",
            doc_id="doc1",
            chunk_index=1,
            content="Sample text chunk 2 content.",
            start_char=50,
            end_char=78,
            token_count=5,
            is_orphan_block=True,
            metadata={"source": "file1.md"},
        ),
    ]


@pytest.fixture
def sample_audit_report() -> AuditReport:
    """Fixture providing sample legacy AuditReport domain model instance."""
    metrics = IngestionMetrics(
        total_docs=1,
        total_chunks=2,
        total_original_chars=100,
        total_chunk_chars=83,
        char_coverage_ratio=0.99,
        duplicate_char_ratio=0.05,
        orphan_block_count=1,
        status="PASSED",
    )
    return AuditReport(
        timestamp="2026-08-09T10:00:00Z",
        strategy_used="recursive",
        metrics=metrics,
        document_ids=["doc1"],
        errors=[],
    )


@pytest.fixture
def sample_ingestion_report() -> IngestionReport:
    """Fixture providing sample structured IngestionReport instance."""
    doc_rpt = DocumentReport(
        document_id="doc1",
        source_path="data/file1.md",
        char_coverage_ratio=1.0,
        chunk_count=2,
        status="ok",
    )
    return IngestionReport(
        corpus_path="data/input",
        strategy_used="recursive",
        documents=[doc_rpt],
        total_chunks=2,
        global_char_coverage_ratio=1.0,
        documents_in_error=0,
        has_blocking_alerts=False,
    )


def test_jsonl_chunk_exporter_export_and_read(
    sample_chunks: list[Chunk], tmp_path: Path
) -> None:
    """Verify JSONLChunkExporter exports chunks and reads them back losslessly."""
    output_file = tmp_path / "nested" / "chunks.jsonl"
    exporter = JSONLChunkExporter()

    result_path = exporter.export(sample_chunks, output_file)
    assert result_path == output_file
    assert output_file.exists()

    loaded_chunks = exporter.read(output_file)
    assert len(loaded_chunks) == len(sample_chunks)
    assert loaded_chunks[0].id == sample_chunks[0].id
    assert loaded_chunks[0].content == sample_chunks[0].content
    assert loaded_chunks[1].is_orphan_block is True


def test_jsonl_chunk_exporter_stream(
    sample_chunks: list[Chunk], tmp_path: Path
) -> None:
    """Verify JSONLChunkExporter streaming export."""
    output_file = tmp_path / "stream_chunks.jsonl"
    exporter = JSONLChunkExporter()

    from collections.abc import Iterator

    def chunk_generator() -> Iterator[Chunk]:
        yield from sample_chunks

    exporter.export_stream(chunk_generator(), output_file)
    lines = output_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2


def test_jsonl_chunk_exporter_missing_file(tmp_path: Path) -> None:
    """Verify reading missing JSONL file raises AuditError."""
    exporter = JSONLChunkExporter()
    with pytest.raises(AuditError, match="not found"):
        exporter.read(tmp_path / "non_existent.jsonl")


def test_audit_report_exporter_audit_report(
    sample_audit_report: AuditReport, tmp_path: Path
) -> None:
    """Verify AuditReportExporter exports and reads AuditReport."""
    output_file = tmp_path / "reports" / "rapport_ingestion.json"
    exporter = AuditReportExporter()

    result_path = exporter.export(sample_audit_report, output_file)
    assert result_path == output_file
    assert output_file.exists()

    loaded_report = exporter.read_audit_report(output_file)
    assert loaded_report.timestamp == sample_audit_report.timestamp
    assert loaded_report.metrics.status == "PASSED"


def test_audit_report_exporter_ingestion_report(
    sample_ingestion_report: IngestionReport, tmp_path: Path
) -> None:
    """Verify AuditReportExporter exports and reads IngestionReport."""
    output_file = tmp_path / "ingestion_report.json"
    exporter = AuditReportExporter()

    exporter.export(sample_ingestion_report, output_file)
    loaded_report = exporter.read_ingestion_report(output_file)

    assert loaded_report.corpus_path == sample_ingestion_report.corpus_path
    assert loaded_report.total_chunks == 2
    assert loaded_report.has_blocking_alerts is False


def test_audit_report_exporter_missing_files(tmp_path: Path) -> None:
    """Verify reading missing report files raises AuditError."""
    exporter = AuditReportExporter()
    with pytest.raises(AuditError, match="not found"):
        exporter.read_audit_report(tmp_path / "missing.json")

    with pytest.raises(AuditError, match="not found"):
        exporter.read_ingestion_report(tmp_path / "missing.json")


def test_procedural_export_helpers(
    sample_chunks: list[Chunk],
    sample_audit_report: AuditReport,
    tmp_path: Path,
) -> None:
    """Verify export_chunks_jsonl and export_audit_report procedural helpers."""
    chunks_path = tmp_path / "helper_chunks.jsonl"
    report_path = tmp_path / "helper_report.json"

    export_chunks_jsonl(sample_chunks, chunks_path)
    export_audit_report(sample_audit_report, report_path)

    assert chunks_path.exists()
    assert report_path.exists()
