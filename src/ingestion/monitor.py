"""Ingestion quality monitor and information loss auditor engine."""

from datetime import datetime, timezone

from ingestion.doc_auditor import DocumentAuditor
from ingestion.models import (
    AuditReport,
    Chunk,
    Document,
    DocumentReport,
    IngestionMetrics,
    IngestionReport,
)
from ingestion.tokenizers import BaseTokenizer, get_tokenizer


class IngestionMonitor:
    """Quality assurance and information loss audit engine."""

    def __init__(
        self,
        min_chunk_size: int = 20,
        max_overlap_tolerance: float = 0.05,
        coverage_threshold: float = 0.98,
        tokenizer: BaseTokenizer | str | None = None,
    ) -> None:
        """Initialize monitor audit thresholds and tokenizer provider."""
        self.min_chunk_size = min_chunk_size
        self.max_overlap_tolerance = max_overlap_tolerance
        self.coverage_threshold = coverage_threshold
        if isinstance(tokenizer, str):
            self.tokenizer: BaseTokenizer | None = get_tokenizer(tokenizer)
        else:
            self.tokenizer = tokenizer or get_tokenizer("gemini")
        self.doc_auditor = DocumentAuditor(
            min_chunk_size=min_chunk_size,
            max_overlap_tolerance=max_overlap_tolerance,
            coverage_threshold=coverage_threshold,
            tokenizer=self.tokenizer,
        )

    def _detect_orphan_blocks(self, cleaned_text: str, chunks: list[Chunk]) -> int:
        """Detect Markdown tables or code blocks split across chunk boundaries."""
        return self.doc_auditor.detect_orphan_blocks(cleaned_text, chunks)

    def _compute_token_delta(
        self,
        cleaned_text: str,
        chunks: list[Chunk],
        source_tokens: int | None = None,
    ) -> int:
        """Calculate token count delta between cleaned text and chunks."""
        return self.doc_auditor.compute_token_delta(cleaned_text, chunks, source_tokens)

    def audit_document(
        self,
        document_id: str,
        source_path: str,
        cleaned_text: str,
        chunks: list[Chunk],
        errors: list[str] | None = None,
        source_tokens: int | None = None,
    ) -> DocumentReport:
        """Audit single document for coverage, duplicate ratio, token delta, and orphan blocks."""
        return self.doc_auditor.audit_document(
            document_id=document_id,
            source_path=source_path,
            cleaned_text=cleaned_text,
            chunks=chunks,
            errors=errors,
            source_tokens=source_tokens,
        )

    def audit(
        self,
        docs: list[Document],
        chunks: list[Chunk],
        strategy_name: str,
        errors: list[str] | None = None,
    ) -> AuditReport:
        """Evaluate document retention, overlap ratios, and orphan block counts across corpus."""
        total_docs = len(docs)
        total_chunks = len(chunks)
        total_orig_chars = sum(d.char_count for d in docs)
        total_chunk_chars = sum(len(c.content) for c in chunks)

        doc_chunks_map: dict[str, list[Chunk]] = {}
        for c in chunks:
            doc_chunks_map.setdefault(c.doc_id, []).append(c)

        total_covered_chars = 0
        doc_reports: list[DocumentReport] = []
        for doc in docs:
            d_chunks = doc_chunks_map.get(doc.id, [])
            report = self.audit_document(
                document_id=doc.id,
                source_path=doc.file_path,
                cleaned_text=doc.content,
                chunks=d_chunks,
            )
            doc_reports.append(report)
            covered: set[int] = set()
            for c in d_chunks:
                for idx in range(max(0, c.start_char), min(len(doc.content), c.end_char)):
                    covered.add(idx)
            total_covered_chars += len(covered)

        coverage_ratio = (
            round(total_covered_chars / total_orig_chars, 4)
            if total_orig_chars > 0
            else 1.0
        )
        orphan_count = sum(r.orphan_blocks for r in doc_reports)
        dup_ratio = round(
            max(0.0, (total_chunk_chars - total_covered_chars) / max(1, total_orig_chars)),
            4,
        )

        passed = (
            (coverage_ratio >= self.coverage_threshold)
            and (orphan_count == 0)
            and not (errors or [])
        )
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

    def create_ingestion_report(
        self,
        corpus_path: str,
        strategy_used: str,
        doc_reports: list[DocumentReport],
    ) -> IngestionReport:
        """Construct aggregated IngestionReport model from per-document audit reports."""
        total_chunks = sum(r.chunk_count for r in doc_reports)
        docs_in_error = sum(1 for r in doc_reports if r.status == "error" or len(r.errors) > 0)
        has_blocking = docs_in_error > 0 or any(r.orphan_blocks > 0 for r in doc_reports)
        avg_coverage = (
            sum(r.char_coverage_ratio for r in doc_reports) / len(doc_reports)
            if doc_reports
            else 1.0
        )
        return IngestionReport(
            corpus_path=corpus_path,
            strategy_used=strategy_used,
            execution_timestamp=datetime.now(timezone.utc),
            documents=doc_reports,
            total_chunks=total_chunks,
            global_char_coverage_ratio=round(avg_coverage, 4),
            documents_in_error=docs_in_error,
            has_blocking_alerts=has_blocking,
        )
