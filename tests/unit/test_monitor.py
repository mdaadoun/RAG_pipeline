"""Unit tests for IngestionMonitor and metrics audit logic."""

from ingestion.models import Chunk, Document
from ingestion.monitor import IngestionMonitor


def test_ingestion_monitor_pass() -> None:
    """Verify monitor produces PASSED status when coverage >= 98% and no orphans."""
    doc = Document(
        id="d1",
        file_path="test.md",
        content="Sample content string for testing retention coverage.",
    )
    chunk = Chunk(
        id="c1",
        doc_id="d1",
        chunk_index=0,
        content="Sample content string for testing retention coverage.",
        start_char=0,
        end_char=len(doc.content),
        token_count=7,
        is_orphan_block=False,
    )
    monitor = IngestionMonitor(coverage_threshold=0.98)
    report = monitor.audit([doc], [chunk], strategy_name="recursive")
    assert report.metrics.status == "PASSED"
    assert report.metrics.char_coverage_ratio >= 0.98


def test_ingestion_monitor_low_coverage_warning() -> None:
    """Verify monitor flags low character coverage ratio (< 98%)."""
    doc = Document(
        id="d2",
        file_path="long_doc.txt",
        content="A" * 1000,
    )
    # Only cover first 500 chars (50% coverage)
    chunk = Chunk(
        id="c1",
        doc_id="d2",
        chunk_index=0,
        content="A" * 500,
        start_char=0,
        end_char=500,
        token_count=100,
        is_orphan_block=False,
    )
    monitor = IngestionMonitor(coverage_threshold=0.98)
    report = monitor.audit([doc], [chunk], strategy_name="fixed")
    assert report.metrics.status == "FAILED"
    assert report.metrics.char_coverage_ratio == 0.5

    doc_report = monitor.audit_document("d2", "long_doc.txt", doc.content, [chunk])
    assert doc_report.status == "warning"


def test_ingestion_monitor_orphan_detection() -> None:
    """Verify orphan Markdown tables split across chunks trigger error status."""
    table_text = (
        "Header text before table\n"
        "| Col1 | Col2 |\n"
        "| --- | --- |\n"
        "| Val1 | Val2 |\n"
        "Footer text after table"
    )
    doc = Document(id="d3", file_path="table.md", content=table_text)

    # Chunk 1 cuts table mid-way
    split_pos = table_text.find("| Val1")
    c1 = Chunk(
        id="c1",
        doc_id="d3",
        chunk_index=0,
        content=table_text[:split_pos],
        start_char=0,
        end_char=split_pos,
        token_count=15,
        is_orphan_block=False,
    )
    c2 = Chunk(
        id="c2",
        doc_id="d3",
        chunk_index=1,
        content=table_text[split_pos:],
        start_char=split_pos,
        end_char=len(table_text),
        token_count=15,
        is_orphan_block=False,
    )

    monitor = IngestionMonitor()
    doc_report = monitor.audit_document("d3", "table.md", table_text, [c1, c2])
    assert doc_report.orphan_blocks > 0
    assert doc_report.status == "error"


def test_audit_document_empty_and_errors() -> None:
    """Verify audit_document behavior on empty document and explicitly passed errors."""
    monitor = IngestionMonitor()
    empty_report = monitor.audit_document("d4", "empty.txt", "", [])
    assert empty_report.char_coverage_ratio == 1.0
    assert empty_report.status == "ok"

    err_report = monitor.audit_document("d5", "bad.txt", "content", [], errors=["File corrupted"])
    assert err_report.status == "error"
    assert err_report.errors == ["File corrupted"]


def test_duplicate_char_ratio_calculation() -> None:
    """Verify duplicate character ratio computation for overlapping chunks."""
    doc_content = "0123456789"
    doc = Document(id="d6", file_path="overlap.txt", content=doc_content)
    # Chunk 1: 0-7, Chunk 2: 3-10 (overlap of 4 chars: '3456')
    c1 = Chunk(
        id="c1",
        doc_id="d6",
        chunk_index=0,
        content="01234567",
        start_char=0,
        end_char=8,
        token_count=2,
    )
    c2 = Chunk(
        id="c2",
        doc_id="d6",
        chunk_index=1,
        content="3456789",
        start_char=3,
        end_char=10,
        token_count=2,
    )
    monitor = IngestionMonitor()
    doc_report = monitor.audit_document("d6", "overlap.txt", doc_content, [c1, c2])
    assert doc_report.char_coverage_ratio == 1.0
    assert doc_report.duplicate_char_ratio == 0.5  # 5 duplicate chars / 10 total


def test_create_ingestion_report() -> None:
    """Verify creation of aggregated IngestionReport model."""
    monitor = IngestionMonitor()
    doc_report = monitor.audit_document("d1", "test.md", "content", [])
    ing_report = monitor.create_ingestion_report("data/input", "recursive", [doc_report])
    assert ing_report.corpus_path == "data/input"
    assert ing_report.strategy_used == "recursive"
    assert ing_report.total_chunks == 0
    assert not ing_report.has_blocking_alerts

