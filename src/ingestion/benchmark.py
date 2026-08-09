"""Comparative strategy benchmark engine comparing Fixed vs Recursive chunking."""

from __future__ import annotations

import time
from pathlib import Path

from pydantic import Field

from ingestion.corpus import SyntheticCorpus
from ingestion.models import BaseDomainModel, IngestionConfig, StrategyType
from ingestion.pipeline import PipelineOrchestrator


class BenchmarkStrategyMetrics(BaseDomainModel):
    """Execution and quality metrics for a single chunking strategy run."""

    strategy: StrategyType = Field(..., description="Chunking strategy evaluated")
    execution_time_ms: float = Field(
        ..., description="Pipeline execution wall-clock time in milliseconds"
    )
    total_documents: int = Field(..., description="Total documents processed")
    total_chunks: int = Field(..., description="Total chunks generated")
    avg_chunk_tokens: float = Field(..., description="Average token count per chunk")
    avg_chunk_chars: float = Field(..., description="Average character count per chunk")
    char_coverage_ratio: float = Field(..., description="Global character coverage ratio")
    duplicate_char_ratio: float = Field(..., description="Global duplicate character ratio")
    orphan_blocks: int = Field(..., description="Count of split/orphan structural blocks")
    token_count_delta: int = Field(
        ..., description="Token count delta between original and chunks"
    )
    blocking_alerts: int = Field(..., description="Number of blocking audit alerts")
    status: str = Field(..., description="Audit status (passed or failed)")


class BenchmarkComparisonResult(BaseDomainModel):
    """Comparative analysis result contrasting fixed vs recursive strategies."""

    fixed_metrics: BenchmarkStrategyMetrics = Field(
        ..., description="Metrics for fixed-size strategy"
    )
    recursive_metrics: BenchmarkStrategyMetrics = Field(
        ..., description="Metrics for recursive strategy"
    )
    winning_strategy: StrategyType = Field(
        ..., description="Recommended strategy based on quality gates"
    )
    coverage_delta: float = Field(
        ..., description="Coverage ratio difference (recursive - fixed)"
    )
    orphan_reduction: int = Field(
        ..., description="Reduction in orphan blocks (fixed - recursive)"
    )
    chunk_count_diff: int = Field(
        ..., description="Difference in chunk count (fixed - recursive)"
    )
    summary_notes: list[str] = Field(
        default_factory=list, description="Summary qualitative observations"
    )


class StrategyBenchmarkRunner:
    """Benchmark runner evaluating Fixed vs Recursive chunking performance."""

    def __init__(self, corpus: SyntheticCorpus | None = None) -> None:
        self._corpus = corpus or SyntheticCorpus()

    def run_benchmark(
        self,
        input_dir: str | Path | None = None,
        chunk_size: int = 512,
        overlap: int = 64,
        min_chunk_size: int = 50,
    ) -> BenchmarkComparisonResult:
        """Run comparative benchmark over corpus directory for fixed and recursive strategies."""
        target_dir = Path(input_dir) if input_dir else self._corpus.fixtures_dir
        if not target_dir.exists() or not any(target_dir.iterdir()):
            self._corpus.ensure_default_fixtures()
            target_dir = self._corpus.fixtures_dir

        fixed_metrics = self._evaluate_strategy(
            StrategyType.FIXED, target_dir, chunk_size, overlap, min_chunk_size
        )
        recursive_metrics = self._evaluate_strategy(
            StrategyType.RECURSIVE, target_dir, chunk_size, overlap, min_chunk_size
        )

        coverage_delta = round(
            recursive_metrics.char_coverage_ratio - fixed_metrics.char_coverage_ratio, 4
        )
        orphan_reduction = fixed_metrics.orphan_blocks - recursive_metrics.orphan_blocks
        chunk_count_diff = fixed_metrics.total_chunks - recursive_metrics.total_chunks

        winning = (
            StrategyType.RECURSIVE
            if (
                recursive_metrics.orphan_blocks < fixed_metrics.orphan_blocks
                or recursive_metrics.char_coverage_ratio >= fixed_metrics.char_coverage_ratio
            )
            else StrategyType.FIXED
        )

        notes = [
            f"Recursive strategy eliminated {orphan_reduction} orphan structural blocks.",
            f"Coverage delta: {coverage_delta:+.4f} in favor of recursive strategy.",
            f"Fixed chunk count: {fixed_metrics.total_chunks} vs Recursive: {recursive_metrics.total_chunks}.",
        ]

        return BenchmarkComparisonResult(
            fixed_metrics=fixed_metrics,
            recursive_metrics=recursive_metrics,
            winning_strategy=winning,
            coverage_delta=coverage_delta,
            orphan_reduction=orphan_reduction,
            chunk_count_diff=chunk_count_diff,
            summary_notes=notes,
        )

    def _evaluate_strategy(
        self,
        strategy: StrategyType,
        input_dir: Path,
        chunk_size: int,
        overlap: int,
        min_chunk_size: int,
    ) -> BenchmarkStrategyMetrics:
        """Evaluate a single strategy using PipelineOrchestrator."""
        config = IngestionConfig(
            strategy=strategy,
            chunk_size=chunk_size,
            overlap=overlap,
            min_chunk_size=min_chunk_size,
            input_dir=str(input_dir),
        )
        orchestrator = PipelineOrchestrator(config)
        start_time = time.perf_counter()
        result = orchestrator.run(input_dir=input_dir)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        report = result.audit_report
        chunks = result.chunks
        total_chunks = len(chunks)
        avg_tokens = (
            sum(c.token_count for c in chunks) / total_chunks if total_chunks > 0 else 0.0
        )
        avg_chars = (
            sum(c.char_count for c in chunks) / total_chunks if total_chunks > 0 else 0.0
        )

        from ingestion.gatekeeper import ExitCodeGatekeeper

        token_delta = sum(r.token_count_delta for r in result.doc_reports)
        gatekeeper = ExitCodeGatekeeper()
        blocking_reasons = gatekeeper.get_blocking_reasons(result)

        return BenchmarkStrategyMetrics(
            strategy=strategy,
            execution_time_ms=round(elapsed_ms, 2),
            total_documents=len(result.documents),
            total_chunks=total_chunks,
            avg_chunk_tokens=round(avg_tokens, 2),
            avg_chunk_chars=round(avg_chars, 2),
            char_coverage_ratio=report.metrics.char_coverage_ratio,
            duplicate_char_ratio=report.metrics.duplicate_char_ratio,
            orphan_blocks=report.metrics.orphan_block_count,
            token_count_delta=token_delta,
            blocking_alerts=len(blocking_reasons),
            status=report.metrics.status,
        )

    def format_markdown_table(self, comparison: BenchmarkComparisonResult) -> str:
        """Format comparison metrics as a GitHub markdown table."""
        fm = comparison.fixed_metrics
        rm = comparison.recursive_metrics
        return (
            "| Metric | FixedSizeChunker | RecursiveStructuralChunker |\n"
            "| --- | --- | --- |\n"
            f"| **Execution Time (ms)** | {fm.execution_time_ms:.2f} ms | {rm.execution_time_ms:.2f} ms |\n"
            f"| **Total Chunks** | {fm.total_chunks} | {rm.total_chunks} |\n"
            f"| **Avg Tokens / Chunk** | {fm.avg_chunk_tokens:.1f} | {rm.avg_chunk_tokens:.1f} |\n"
            f"| **Avg Chars / Chunk** | {fm.avg_chunk_chars:.1f} | {rm.avg_chunk_chars:.1f} |\n"
            f"| **Char Coverage Ratio** | {fm.char_coverage_ratio:.4f} | {rm.char_coverage_ratio:.4f} |\n"
            f"| **Duplicate Char Ratio** | {fm.duplicate_char_ratio:.4f} | {rm.duplicate_char_ratio:.4f} |\n"
            f"| **Orphan Blocks** | {fm.orphan_blocks} | {rm.orphan_blocks} |\n"
            f"| **Blocking Alerts** | {fm.blocking_alerts} | {rm.blocking_alerts} |\n"
            f"| **Audit Status** | {fm.status} | {rm.status} |\n"
        )
