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
