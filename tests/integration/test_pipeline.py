"""Integration tests for global pipeline execution and exporters."""

from pathlib import Path

from ingestion.exporters import AuditReportExporter, JSONLChunkExporter
from ingestion.pipeline import IngestionPipeline, PipelineOrchestrator


def test_pipeline_execution(fixtures_dir: Path, tmp_path: Path) -> None:
    """Verify end-to-end pipeline execution creates chunks.jsonl and audit report."""
    output_dir = tmp_path / "output"
    report_file = tmp_path / "report.json"

    pipeline = IngestionPipeline(strategy_name="recursive", chunk_size=200)
    report = pipeline.run(
        input_dir=fixtures_dir,
        output_dir=output_dir,
        report_path=report_file,
    )

    chunks_file = output_dir / "chunks.jsonl"
    assert chunks_file.exists()
    assert report_file.exists()
    assert report.metrics.total_docs > 0
    assert report.metrics.total_chunks > 0

    chunk_exporter = JSONLChunkExporter()
    chunks = chunk_exporter.read(chunks_file)
    assert len(chunks) == report.metrics.total_chunks

    report_exporter = AuditReportExporter()
    loaded_report = report_exporter.read_audit_report(report_file)
    assert loaded_report.metrics.total_docs == report.metrics.total_docs


def test_pipeline_orchestrator_exporter_integration(
    fixtures_dir: Path, tmp_path: Path
) -> None:
    """Verify PipelineOrchestrator uses exporters to write valid artifacts."""
    output_dir = tmp_path / "orch_output"
    report_file = tmp_path / "rapport_ingestion.json"

    orchestrator = PipelineOrchestrator()
    result = orchestrator.run(
        input_dir=fixtures_dir,
        output_dir=output_dir,
        report_path=report_file,
    )

    chunks_file = output_dir / "chunks.jsonl"
    assert chunks_file.exists()
    assert report_file.exists()

    chunks = JSONLChunkExporter().read(chunks_file)
    assert len(chunks) == len(result.chunks)

    audit_rpt = AuditReportExporter().read_audit_report(report_file)
    assert audit_rpt.metrics.total_chunks == len(result.chunks)

