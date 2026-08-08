"""Integration tests for global pipeline execution."""

from pathlib import Path

from ingestion.pipeline import IngestionPipeline


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

    assert (output_dir / "chunks.jsonl").exists()
    assert report_file.exists()
    assert report.metrics.total_docs > 0
    assert report.metrics.total_chunks > 0
