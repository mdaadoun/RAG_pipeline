"""Ingestion quality monitor and information loss auditor engine."""

from datetime import datetime, timezone

from ingestion.models import AuditReport, Chunk, Document, IngestionMetrics


class IngestionMonitor:
    """Quality assurance and information loss audit engine."""

    def __init__(self, coverage_threshold: float = 0.98) -> None:
        self.coverage_threshold = coverage_threshold

    def audit(
        self,
        docs: list[Document],
        chunks: list[Chunk],
        strategy_name: str,
        errors: list[str] | None = None,
    ) -> AuditReport:
        """Evaluate document retention, overlap ratios, and orphan block counts."""
        total_docs = len(docs)
        total_chunks = len(chunks)
        total_orig_chars = sum(d.char_count for d in docs)
        total_chunk_chars = sum(len(c.content) for c in chunks)

        coverage_ratio = (
            round(total_chunk_chars / total_orig_chars, 4)
            if total_orig_chars > 0
            else 1.0
        )

        orphan_count = sum(1 for c in chunks if c.is_orphan_block)
        dup_ratio = round(
            max(0.0, (total_chunk_chars - total_orig_chars) / max(1, total_orig_chars)),
            4,
        )

        passed = (coverage_ratio >= self.coverage_threshold) and (orphan_count == 0)
        status = "PASSED" if passed else "FAILED"

        metrics = IngestionMetrics(
            total_docs=total_docs,
            total_chunks=total_chunks,
            total_original_chars=total_orig_chars,
            total_chunk_chars=total_chunk_chars,
            char_coverage_ratio=coverage_ratio,
            duplicate_char_ratio=dup_ratio,
            orphan_block_count=orphan_count,
            status=status,
        )

        return AuditReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            strategy_used=strategy_name,
            metrics=metrics,
            document_ids=[d.id for d in docs],
            errors=errors or [],
        )
