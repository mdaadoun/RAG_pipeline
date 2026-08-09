"""Pipeline orchestrator facade coordinating ingestion stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from config.logging import get_logger
from ingestion.chunkers import BaseChunker, FixedSizeChunker, RecursiveStructuralChunker
from ingestion.cleaner import TextCleaner
from ingestion.file_shield import FileShieldContext, IngestionStage
from ingestion.loaders import DocumentLoader, get_loader
from ingestion.models import (
    AuditReport,
    Chunk,
    Document,
    DocumentReport,
    IngestionConfig,
    IngestionReport,
    LoadedDocument,
)
from ingestion.monitor import IngestionMonitor
from ingestion.utils.json_utils import save_audit_report, save_chunks_jsonl

logger = get_logger("pipeline")


@dataclass(frozen=True)
class PipelineResult:
    """Immutable result container returned by orchestrator."""

    audit_report: AuditReport
    ingestion_report: IngestionReport
    documents: list[Document] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)
    doc_reports: list[DocumentReport] = field(default_factory=list)


def _build_chunker(config: IngestionConfig) -> BaseChunker:
    """Factory: select chunking strategy from config."""
    tokenizer_name = config.tokenizer.value
    if config.strategy.value == "fixed":
        return FixedSizeChunker(
            config.chunk_size, config.overlap, config.min_chunk_size,
            tokenizer=tokenizer_name,
        )
    return RecursiveStructuralChunker(
        config.chunk_size, config.overlap, config.min_chunk_size,
        tokenizer=tokenizer_name,
    )


def _discover_files(input_path: Path) -> list[Path]:
    """Collect all regular files under input directory."""
    return sorted(p for p in input_path.glob("**/*") if p.is_file())


class PipelineOrchestrator:
    """Facade coordinating Loaders → Cleaner → Chunkers → Monitor → Exporters."""

    def __init__(self, config: IngestionConfig | None = None) -> None:
        self._config = config or IngestionConfig()
        self._cleaner = TextCleaner()
        self._chunker = _build_chunker(self._config)
        self._monitor = IngestionMonitor(
            coverage_threshold=self._config.coverage_threshold,
        )

    @property
    def config(self) -> IngestionConfig:
        """Expose read-only pipeline configuration."""
        return self._config

    def run(
        self,
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        report_path: str | Path | None = None,
    ) -> PipelineResult:
        """Execute full ingestion pipeline over target directory."""
        in_path = Path(input_dir or self._config.input_dir)
        out_path = Path(output_dir or self._config.output_dir)
        rpt_path = Path(report_path or self._config.report_path)
        out_path.mkdir(parents=True, exist_ok=True)

        docs, chunks, doc_reports = self._process_corpus(in_path)
        strategy_name = self._config.strategy.value

        save_chunks_jsonl(chunks, out_path / "chunks.jsonl")
        audit_report = self._monitor.audit(docs, chunks, strategy_name)
        save_audit_report(audit_report, rpt_path)

        ingestion_report = self._monitor.create_ingestion_report(
            corpus_path=str(in_path),
            strategy_used=strategy_name,
            doc_reports=doc_reports,
        )

        self._log_summary(docs, chunks, audit_report)
        return PipelineResult(
            audit_report=audit_report,
            ingestion_report=ingestion_report,
            documents=docs,
            chunks=chunks,
            doc_reports=doc_reports,
        )

    def _process_corpus(
        self, input_path: Path,
    ) -> tuple[list[Document], list[Chunk], list[DocumentReport]]:
        """Load, clean, chunk, and audit each file in corpus."""
        docs: list[Document] = []
        chunks: list[Chunk] = []
        doc_reports: list[DocumentReport] = []

        for file_path in _discover_files(input_path):
            doc, file_chunks, report = self._process_single_file(file_path)
            if doc is not None:
                docs.append(doc)
                chunks.extend(file_chunks)
            doc_reports.append(report)

        return docs, chunks, doc_reports

    def _process_single_file(
        self, file_path: Path,
    ) -> tuple[Document | None, list[Chunk], DocumentReport]:
        """Process one file through load → clean → chunk → audit stages.

        Each sub-stage is individually shielded so failures record
        tracebacks into DocumentReport.errors without crashing the batch.
        """
        ctx = FileShieldContext(file_path=file_path)

        # Stage: LOAD
        loader = self._shield_load(file_path, ctx)
        if loader is None:
            return None, [], self._error_report(file_path, ctx)

        raw_doc = self._shield_read(loader, file_path, ctx)
        if raw_doc is None:
            return None, [], self._error_report(file_path, ctx)

        # Stage: CLEAN
        cleaned = self._shield_clean(raw_doc.content, file_path, ctx)
        if cleaned is None:
            return None, [], self._error_report(file_path, ctx)

        doc = Document(
            id=raw_doc.id,
            file_path=raw_doc.file_path,
            content=cleaned,
            metadata=raw_doc.metadata,
        )

        # Stage: CHUNK
        file_chunks = self._shield_chunk(doc, file_path, ctx)
        if file_chunks is None:
            return None, [], self._error_report(file_path, ctx)

        # Stage: AUDIT
        report = self._shield_audit(doc, file_chunks, ctx)
        return doc, file_chunks, report

    def _shield_load(
        self,
        file_path: Path,
        ctx: FileShieldContext,
    ) -> "DocumentLoader | None":
        """Shield: resolve loader for file extension."""
        try:
            return get_loader(file_path)
        except Exception as exc:
            ctx.record_error(IngestionStage.LOAD, exc)
            return None

    def _shield_read(
        self,
        loader: "DocumentLoader",
        file_path: Path,
        ctx: FileShieldContext,
    ) -> "LoadedDocument | None":
        """Shield: read raw document content from disk."""
        try:
            return loader.load()
        except Exception as exc:
            ctx.record_error(IngestionStage.LOAD, exc)
            return None

    def _shield_clean(
        self,
        raw_content: str,
        file_path: Path,
        ctx: FileShieldContext,
    ) -> str | None:
        """Shield: clean and normalize raw text."""
        try:
            return self._cleaner.clean(raw_content)
        except Exception as exc:
            ctx.record_error(IngestionStage.CLEAN, exc)
            return None

    def _shield_chunk(
        self,
        doc: Document,
        file_path: Path,
        ctx: FileShieldContext,
    ) -> list[Chunk] | None:
        """Shield: chunk cleaned document."""
        try:
            return self._chunker.chunk(doc)
        except Exception as exc:
            ctx.record_error(IngestionStage.CHUNK, exc)
            return None

    def _shield_audit(
        self,
        doc: Document,
        file_chunks: list[Chunk],
        ctx: FileShieldContext,
    ) -> DocumentReport:
        """Shield: audit document quality; fallback to error report."""
        try:
            return self._monitor.audit_document(
                document_id=doc.id,
                source_path=doc.file_path,
                cleaned_text=doc.content,
                chunks=file_chunks,
            )
        except Exception as exc:
            ctx.record_error(IngestionStage.AUDIT, exc)
            return self._error_report(
                Path(doc.file_path), ctx,
            )

    def _error_report(
        self,
        file_path: Path,
        ctx: FileShieldContext,
    ) -> DocumentReport:
        """Build error DocumentReport from accumulated shield context."""
        return DocumentReport(
            document_id=f"error_{file_path.name}",
            source_path=str(file_path),
            status="error",
            errors=ctx.format_error_messages(),
        )

    def _log_summary(
        self,
        docs: list[Document],
        chunks: list[Chunk],
        report: AuditReport,
    ) -> None:
        """Emit structured log for pipeline completion."""
        logger.info(
            "pipeline_complete",
            docs=len(docs),
            chunks=len(chunks),
            coverage=report.metrics.char_coverage_ratio,
            status=report.metrics.status,
        )


class IngestionPipeline:
    """Backward-compatible wrapper delegating to PipelineOrchestrator."""

    def __init__(
        self,
        strategy_name: str = "recursive",
        chunk_size: int = 512,
        overlap: int = 64,
        min_chunk_size: int = 50,
    ) -> None:
        from ingestion.models import StrategyType

        strategy = (
            StrategyType.FIXED if strategy_name == "fixed" else StrategyType.RECURSIVE
        )
        self._config = IngestionConfig(
            strategy=strategy,
            chunk_size=chunk_size,
            overlap=overlap,
            min_chunk_size=min_chunk_size,
        )
        self._orchestrator = PipelineOrchestrator(self._config)

    def run(
        self,
        input_dir: str | Path,
        output_dir: str | Path,
        report_path: str | Path = "rapport_ingestion.json",
    ) -> AuditReport:
        """Run pipeline, return legacy AuditReport for CLI compatibility."""
        result = self._orchestrator.run(input_dir, output_dir, report_path)
        return result.audit_report
