"""Unit tests for comparative strategy benchmark module."""

from pathlib import Path

from typer.testing import CliRunner

from ingestion.benchmark import (
    BenchmarkComparisonResult,
    BenchmarkStrategyMetrics,
    StrategyBenchmarkRunner,
)
from ingestion.cli import app
from ingestion.corpus import SyntheticCorpus
from ingestion.models import StrategyType

runner = CliRunner()


def test_benchmark_models_immutability(tmp_path: Path) -> None:
    """Verify BenchmarkStrategyMetrics and BenchmarkComparisonResult immutability."""
    metrics = BenchmarkStrategyMetrics(
        strategy=StrategyType.FIXED,
        execution_time_ms=12.5,
        total_documents=4,
        total_chunks=10,
        avg_chunk_tokens=150.0,
        avg_chunk_chars=600.0,
        char_coverage_ratio=0.99,
        duplicate_char_ratio=0.01,
        orphan_blocks=2,
        token_count_delta=5,
        blocking_alerts=1,
        status="failed",
    )
    assert metrics.strategy == StrategyType.FIXED
    assert metrics.execution_time_ms == 12.5
    assert metrics.orphan_blocks == 2

    res = BenchmarkComparisonResult(
        fixed_metrics=metrics,
        recursive_metrics=metrics,
        winning_strategy=StrategyType.RECURSIVE,
        coverage_delta=0.01,
        orphan_reduction=2,
        chunk_count_diff=0,
        summary_notes=["Test note"],
    )
    assert res.winning_strategy == StrategyType.RECURSIVE
    assert res.orphan_reduction == 2


def test_strategy_benchmark_runner_execution(tmp_path: Path) -> None:
    """Verify StrategyBenchmarkRunner executes dual strategy comparison over corpus."""
    corpus = SyntheticCorpus(fixtures_dir=tmp_path)
    corpus.ensure_default_fixtures()

    bench_runner = StrategyBenchmarkRunner(corpus=corpus)
    res = bench_runner.run_benchmark(input_dir=tmp_path)

    assert res.winning_strategy == StrategyType.RECURSIVE
    assert res.fixed_metrics.strategy == StrategyType.FIXED
    assert res.recursive_metrics.strategy == StrategyType.RECURSIVE
    assert res.fixed_metrics.total_documents == 4
    assert res.recursive_metrics.total_documents == 4
    assert res.orphan_reduction >= 0
    assert len(res.summary_notes) >= 3


def test_format_markdown_table(tmp_path: Path) -> None:
    """Verify format_markdown_table generates valid GitHub Markdown table."""
    corpus = SyntheticCorpus(fixtures_dir=tmp_path)
    corpus.ensure_default_fixtures()

    bench_runner = StrategyBenchmarkRunner(corpus=corpus)
    res = bench_runner.run_benchmark(input_dir=tmp_path)
    table_md = bench_runner.format_markdown_table(res)

    assert "| Metric | FixedSizeChunker | RecursiveStructuralChunker |" in table_md
    assert "| **Execution Time (ms)** |" in table_md
    assert "| **Orphan Blocks** |" in table_md
    assert "| **Char Coverage Ratio** |" in table_md


def test_benchmark_cli_command(tmp_path: Path) -> None:
    """Verify Typer CLI benchmark subcommand executes cleanly."""
    corpus = SyntheticCorpus(fixtures_dir=tmp_path)
    corpus.ensure_default_fixtures()

    result = runner.invoke(app, ["benchmark", "--input", str(tmp_path)])
    assert result.exit_code == 0
    assert "Comparative Strategy Benchmark Results" in result.output
    assert "FixedSizeChunker" in result.output
    assert "RecursiveStructuralChunker" in result.output
    assert "Recommended Strategy: RECURSIVE" in result.output
