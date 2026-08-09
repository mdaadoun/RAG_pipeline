"""Unit tests for PipelineOrchestrator facade and backward-compat wrapper."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ingestion.models import (
    AuditReport,
    Chunk,
    Document,
    DocumentReport,
    IngestionConfig,
    IngestionMetrics,
    IngestionReport,
    StrategyType,
)
from ingestion.pipeline import (
    IngestionPipeline,
    PipelineOrchestrator,
    PipelineResult,
    _build_chunker,
    _discover_files,
)


# --- Config & Factory Tests ---


def test_build_chunker_fixed() -> None:
    """Verify fixed strategy config produces FixedSizeChunker."""
    from ingestion.chunkers import FixedSizeChunker

    config = IngestionConfig(strategy=StrategyType.FIXED)
    chunker = _build_chunker(config)
    assert isinstance(chunker, FixedSizeChunker)


def test_build_chunker_recursive_default() -> None:
    """Verify default config produces RecursiveStructuralChunker."""
    from ingestion.chunkers import RecursiveStructuralChunker

    config = IngestionConfig()
    chunker = _build_chunker(config)
    assert isinstance(chunker, RecursiveStructuralChunker)


def test_discover_files_empty_dir(tmp_path: Path) -> None:
    """Verify empty directory returns no files."""
    assert _discover_files(tmp_path) == []


def test_discover_files_recursive(tmp_path: Path) -> None:
    """Verify recursive file discovery under nested directories."""
    (tmp_path / "a.md").write_text("doc a")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("doc b")
    files = _discover_files(tmp_path)
    assert len(files) == 2
    assert all(f.is_file() for f in files)


# --- PipelineResult Immutability ---


def test_pipeline_result_immutable() -> None:
    """Verify PipelineResult is frozen dataclass."""
    metrics = IngestionMetrics(
        total_docs=0, total_chunks=0, total_original_chars=0,
        total_chunk_chars=0, char_coverage_ratio=1.0,
        duplicate_char_ratio=0.0, orphan_block_count=0, status="PASSED",
    )
    audit = AuditReport(
        timestamp="2026-01-01T00:00:00Z", strategy_used="recursive",
        metrics=metrics,
    )
    ing = IngestionReport(
        corpus_path=".", strategy_used="recursive",
    )
    result = PipelineResult(audit_report=audit, ingestion_report=ing)
    with pytest.raises(AttributeError):
        result.audit_report = audit  # type: ignore[misc]


# --- Orchestrator Init ---


def test_orchestrator_default_config() -> None:
    """Verify orchestrator initializes with default IngestionConfig."""
    orch = PipelineOrchestrator()
    assert orch.config.strategy == StrategyType.RECURSIVE
    assert orch.config.chunk_size == 512


def test_orchestrator_custom_config() -> None:
    """Verify orchestrator accepts custom IngestionConfig."""
    cfg = IngestionConfig(
        strategy=StrategyType.FIXED, chunk_size=256, overlap=32,
    )
    orch = PipelineOrchestrator(cfg)
    assert orch.config.strategy == StrategyType.FIXED
    assert orch.config.chunk_size == 256


# --- Orchestrator End-to-End on Fixtures ---


def test_orchestrator_run_with_fixtures(
    fixtures_dir: Path, tmp_path: Path,
) -> None:
    """Verify full orchestrator run produces output files and valid result."""
    cfg = IngestionConfig(
        strategy=StrategyType.RECURSIVE, chunk_size=200,
    )
    orch = PipelineOrchestrator(cfg)
    out = tmp_path / "out"
    rpt = tmp_path / "report.json"

    result = orch.run(input_dir=fixtures_dir, output_dir=out, report_path=rpt)

    assert isinstance(result, PipelineResult)
    assert (out / "chunks.jsonl").exists()
    assert rpt.exists()
    assert result.audit_report.metrics.total_docs > 0
    assert result.audit_report.metrics.total_chunks > 0
    assert len(result.documents) > 0
    assert len(result.chunks) > 0
    assert len(result.doc_reports) > 0


def test_orchestrator_ingestion_report_populated(
    fixtures_dir: Path, tmp_path: Path,
) -> None:
    """Verify IngestionReport is populated with per-document details."""
    orch = PipelineOrchestrator(
        IngestionConfig(chunk_size=200),
    )
    result = orch.run(
        input_dir=fixtures_dir,
        output_dir=tmp_path / "out",
        report_path=tmp_path / "rpt.json",
    )

    ir = result.ingestion_report
    assert isinstance(ir, IngestionReport)
    assert ir.strategy_used == "recursive"
    assert ir.corpus_path == str(fixtures_dir)
    assert len(ir.documents) == len(result.doc_reports)


# --- Unsupported Format Shielding ---


def test_orchestrator_skips_unsupported_files(tmp_path: Path) -> None:
    """Verify orchestrator emits error report for unsupported file types."""
    (tmp_path / "image.png").write_bytes(b"\x89PNG")
    (tmp_path / "doc.md").write_text("# Valid Doc\n\nContent here.")

    out = tmp_path / "out"
    rpt = tmp_path / "rpt.json"
    orch = PipelineOrchestrator(IngestionConfig(chunk_size=200))
    result = orch.run(input_dir=tmp_path, output_dir=out, report_path=rpt)

    assert len(result.documents) == 1
    error_reports = [r for r in result.doc_reports if r.status == "error"]
    assert len(error_reports) >= 1
    assert any("Unsupported" in e for r in error_reports for e in r.errors)


# --- Empty Corpus ---


def test_orchestrator_empty_corpus(tmp_path: Path) -> None:
    """Verify orchestrator handles empty input directory gracefully."""
    inp = tmp_path / "empty"
    inp.mkdir()
    out = tmp_path / "out"
    rpt = tmp_path / "rpt.json"
    orch = PipelineOrchestrator()
    result = orch.run(input_dir=inp, output_dir=out, report_path=rpt)

    assert result.documents == []
    assert result.chunks == []
    assert (out / "chunks.jsonl").exists()


# --- Fixed Strategy Run ---


def test_orchestrator_fixed_strategy(
    fixtures_dir: Path, tmp_path: Path,
) -> None:
    """Verify orchestrator works with fixed chunking strategy."""
    cfg = IngestionConfig(strategy=StrategyType.FIXED, chunk_size=200)
    orch = PipelineOrchestrator(cfg)
    result = orch.run(
        input_dir=fixtures_dir,
        output_dir=tmp_path / "out",
        report_path=tmp_path / "rpt.json",
    )
    assert result.audit_report.strategy_used == "fixed"
    assert result.audit_report.metrics.total_chunks > 0


# --- Error Report Generation ---


def test_error_report_structure() -> None:
    """Verify _error_report produces valid DocumentReport."""
    orch = PipelineOrchestrator()
    rpt = orch._error_report(Path("/fake/file.txt"), "Test error")
    assert rpt.status == "error"
    assert rpt.errors == ["Test error"]
    assert "file.txt" in rpt.document_id


# --- Backward-Compat IngestionPipeline Wrapper ---


def test_legacy_pipeline_returns_audit_report(
    fixtures_dir: Path, tmp_path: Path,
) -> None:
    """Verify IngestionPipeline backward compat returns AuditReport."""
    pipeline = IngestionPipeline(
        strategy_name="recursive", chunk_size=200,
    )
    report = pipeline.run(
        input_dir=fixtures_dir,
        output_dir=tmp_path / "out",
        report_path=tmp_path / "rpt.json",
    )
    assert isinstance(report, AuditReport)
    assert report.metrics.total_docs > 0


def test_legacy_pipeline_fixed_strategy(
    fixtures_dir: Path, tmp_path: Path,
) -> None:
    """Verify IngestionPipeline wrapper works with fixed strategy."""
    pipeline = IngestionPipeline(strategy_name="fixed", chunk_size=200)
    report = pipeline.run(
        input_dir=fixtures_dir,
        output_dir=tmp_path / "out",
        report_path=tmp_path / "rpt.json",
    )
    assert isinstance(report, AuditReport)
    assert report.strategy_used == "fixed"
