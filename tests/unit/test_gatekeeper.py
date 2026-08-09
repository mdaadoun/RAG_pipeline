"""Unit tests for ExitCodeGatekeeper in ingestion/gatekeeper.py."""

from datetime import datetime, timezone

from ingestion.gatekeeper import ExitCodeGatekeeper
from ingestion.models import (
    AuditReport,
    DocumentReport,
    IngestionMetrics,
    IngestionReport,
)
from ingestion.pipeline import PipelineResult


def _create_sample_result(
    *,
    status: str = "PASSED",
    has_blocking_alerts: bool = False,
    documents_in_error: int = 0,
    global_coverage: float = 1.0,
    orphan_blocks: int = 0,
    doc_status: str = "ok",
    errors: list[str] | None = None,
) -> PipelineResult:
    """Helper creating a PipelineResult for testing gatekeeper criteria."""
    doc_rpt = DocumentReport(
        document_id="doc_1",
        source_path="test.md",
        char_coverage_ratio=global_coverage,
        orphan_blocks=orphan_blocks,
        status=doc_status,
        errors=errors or [],
    )
    ing_report = IngestionReport(
        corpus_path="data/input",
        strategy_used="recursive",
        execution_timestamp=datetime.now(timezone.utc),
        documents=[doc_rpt],
        total_chunks=5,
        global_char_coverage_ratio=global_coverage,
        documents_in_error=documents_in_error,
        has_blocking_alerts=has_blocking_alerts,
    )
    metrics = IngestionMetrics(
        total_docs=1,
        total_chunks=5,
        total_original_chars=500,
        total_chunk_chars=500,
        char_coverage_ratio=global_coverage,
        duplicate_char_ratio=0.0,
        orphan_block_count=orphan_blocks,
        status=status,
    )
    audit_report = AuditReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        strategy_used="recursive",
        metrics=metrics,
        document_ids=["doc_1"],
        errors=errors or [],
    )
    return PipelineResult(
        audit_report=audit_report,
        ingestion_report=ing_report,
        documents=[],
        chunks=[],
        doc_reports=[doc_rpt],
    )


def test_gatekeeper_pass_clean_result() -> None:
    """Verify gatekeeper evaluates clean pipeline result to exit code 0."""
    res = _create_sample_result()
    gk = ExitCodeGatekeeper(coverage_threshold=0.98)
    assert not gk.should_exit(res)
    assert gk.evaluate(res) == 0
    assert gk.get_blocking_reasons(res) == []


def test_gatekeeper_fail_has_blocking_alerts() -> None:
    """Verify gatekeeper fails when has_blocking_alerts is True."""
    res = _create_sample_result(has_blocking_alerts=True, status="FAILED")
    gk = ExitCodeGatekeeper()
    assert gk.should_exit(res) is True
    assert gk.evaluate(res) == 1
    assert len(gk.get_blocking_reasons(res)) > 0


def test_gatekeeper_fail_audit_metrics_status_failed() -> None:
    """Verify gatekeeper returns exit code 1 when audit metrics status is FAILED."""
    res = _create_sample_result(status="FAILED")
    gk = ExitCodeGatekeeper()
    assert gk.should_exit(res) is True
    assert gk.evaluate(res) == 1
    reasons = gk.get_blocking_reasons(res)
    assert any("Audit metric status" in r for r in reasons)


def test_gatekeeper_fail_documents_in_error() -> None:
    """Verify gatekeeper captures processing errors in reasons list."""
    res = _create_sample_result(
        documents_in_error=1, doc_status="error", errors=["File corrupted"]
    )
    gk = ExitCodeGatekeeper()
    assert gk.should_exit(res) is True
    assert gk.evaluate(res) == 1
    reasons = gk.get_blocking_reasons(res)
    assert any("Processing errors encountered in 1 document(s)" in r for r in reasons)


def test_gatekeeper_fail_orphan_blocks() -> None:
    """Verify gatekeeper captures orphaned markdown tables or code blocks."""
    res = _create_sample_result(orphan_blocks=2, has_blocking_alerts=True)
    gk = ExitCodeGatekeeper()
    assert gk.should_exit(res) is True
    assert gk.evaluate(res) == 1
    reasons = gk.get_blocking_reasons(res)
    assert any("Detected 2 orphaned Markdown table or code block(s)" in r for r in reasons)


def test_gatekeeper_fail_low_coverage() -> None:
    """Verify gatekeeper captures global coverage dropping below threshold."""
    res = _create_sample_result(global_coverage=0.90)
    gk = ExitCodeGatekeeper(coverage_threshold=0.98)
    assert gk.should_exit(res) is True
    assert gk.evaluate(res) == 1
    reasons = gk.get_blocking_reasons(res)
    assert any("Global character coverage ratio" in r for r in reasons)


def test_gatekeeper_generic_blocking_fallback() -> None:
    """Verify fallback reason when generic has_blocking_alerts is set."""
    res = _create_sample_result(has_blocking_alerts=True)
    gk = ExitCodeGatekeeper()
    reasons = gk.get_blocking_reasons(res)
    assert "Generic blocking alert flag set on ingestion report" in reasons
