"""Unit tests for Rich console UI renderer in ingestion/console.py."""

from rich.console import Console

from ingestion.console import RichConsoleRenderer
from ingestion.models import (
    AuditReport,
    DocumentReport,
    IngestionMetrics,
    IngestionReport,
)
from ingestion.pipeline import PipelineResult


def test_render_header() -> None:
    """Verify header panel contains strategy and input directory."""
    renderer = RichConsoleRenderer()
    panel = renderer.render_header("recursive", "./data/input")
    assert "RAG Ingestion Pipeline Engine" in str(panel.renderable)
    assert "recursive" in str(panel.renderable)


def test_render_document_table() -> None:
    """Verify per-file audit breakdown table renders all required columns."""
    doc_reports = [
        DocumentReport(
            document_id="doc1",
            source_path="/path/to/file1.md",
            char_coverage_ratio=1.0,
            duplicate_char_ratio=0.0,
            orphan_blocks=0,
            token_count_delta=5,
            undersized_chunks_ratio=0.0,
            chunk_count=3,
            status="ok",
        ),
        DocumentReport(
            document_id="doc2",
            source_path="/path/to/file2.md",
            char_coverage_ratio=0.85,
            duplicate_char_ratio=0.05,
            orphan_blocks=2,
            token_count_delta=-3,
            undersized_chunks_ratio=0.1,
            chunk_count=4,
            status="warning",
        ),
    ]

    renderer = RichConsoleRenderer()
    table = renderer.render_document_table(doc_reports)

    assert table.title == "📄 Per-File Audit Breakdown"
    col_names = [col.header for col in table.columns]
    assert "Document" in col_names
    assert "Chunks" in col_names
    assert "Coverage" in col_names
    assert "Orphan Blocks" in col_names
    assert "Token Delta" in col_names
    assert "Status" in col_names


def test_render_summary_table() -> None:
    """Verify summary table renders aggregate audit metrics correctly."""
    audit_report = AuditReport(
        timestamp="2026-08-09T10:00:00Z",
        strategy_used="recursive",
        metrics=IngestionMetrics(
            total_docs=2,
            total_chunks=7,
            total_original_chars=1000,
            total_chunk_chars=990,
            char_coverage_ratio=0.99,
            duplicate_char_ratio=0.01,
            orphan_block_count=0,
            status="PASSED",
        ),
    )
    ingestion_report = IngestionReport(
        corpus_path="./data/input",
        strategy_used="recursive",
        documents=[],
        total_chunks=7,
        global_char_coverage_ratio=0.99,
        documents_in_error=0,
        has_blocking_alerts=False,
    )

    renderer = RichConsoleRenderer()
    table = renderer.render_summary_table(audit_report, ingestion_report)
    assert table.title == "📈 Ingestion Audit Results Summary"


def test_render_pipeline_result_output() -> None:
    """Verify pipeline result renders document breakdown and summary tables to console."""
    console = Console(record=True, width=120)
    renderer = RichConsoleRenderer(console=console)

    doc_report = DocumentReport(
        document_id="doc1",
        source_path="sample.md",
        char_coverage_ratio=0.99,
        orphan_blocks=0,
        token_count_delta=0,
        chunk_count=2,
        status="ok",
    )
    audit_report = AuditReport(
        timestamp="2026-08-09T10:00:00Z",
        strategy_used="recursive",
        metrics=IngestionMetrics(
            total_docs=1,
            total_chunks=2,
            total_original_chars=500,
            total_chunk_chars=500,
            char_coverage_ratio=1.0,
            duplicate_char_ratio=0.0,
            orphan_block_count=0,
            status="PASSED",
        ),
    )
    ingestion_report = IngestionReport(
        corpus_path="sample_dir",
        strategy_used="recursive",
        documents=[doc_report],
        total_chunks=2,
        global_char_coverage_ratio=1.0,
        documents_in_error=0,
        has_blocking_alerts=False,
    )

    result = PipelineResult(
        audit_report=audit_report,
        ingestion_report=ingestion_report,
        doc_reports=[doc_report],
    )

    renderer.render_pipeline_result(result)
    output = console.export_text()

    assert "Per-File Audit Breakdown" in output
    assert "Ingestion Audit Results" in output
    assert "sample.md" in output
    assert "PASSED" in output
