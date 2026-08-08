"""Global document ingestion orchestrator pipeline."""

from pathlib import Path

from config.logging import get_logger
from ingestion.chunkers import BaseChunker, FixedSizeChunker, RecursiveStructuralChunker
from ingestion.cleaner import TextCleaner
from ingestion.loaders import MarkdownLoader, TextLoader
from ingestion.models import AuditReport, Chunk, Document
from ingestion.monitor import IngestionMonitor
from ingestion.utils.json_utils import save_audit_report, save_chunks_jsonl

logger = get_logger("pipeline")


class IngestionPipeline:
    """End-to-end document ingestion & information loss audit pipeline."""

    def __init__(
        self,
        strategy_name: str = "recursive",
        chunk_size: int = 512,
        overlap: int = 64,
        min_chunk_size: int = 50,
    ) -> None:
        self.strategy_name = strategy_name
        self.cleaner = TextCleaner()
        self.monitor = IngestionMonitor()

        if strategy_name == "fixed":
            self.chunker: BaseChunker = FixedSizeChunker(chunk_size, overlap, min_chunk_size)
        else:
            self.chunker = RecursiveStructuralChunker(chunk_size, overlap, min_chunk_size)

    def run(
        self,
        input_dir: str | Path,
        output_dir: str | Path,
        report_path: str | Path = "rapport_ingestion.json",
    ) -> AuditReport:
        """Run full pipeline over target directory."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        docs: list[Document] = []
        chunks: list[Chunk] = []

        files = list(input_path.glob("**/*"))
        for file in files:
            if not file.is_file():
                continue
            if file.suffix in [".md", ".markdown"]:
                loader = MarkdownLoader(file)
            elif file.suffix in [".txt", ".text"]:
                loader = TextLoader(file)
            else:
                continue

            doc = loader.load()
            cleaned_content = self.cleaner.clean(doc.content)
            doc_cleaned = Document(
                id=doc.id,
                file_path=doc.file_path,
                content=cleaned_content,
                metadata=doc.metadata,
            )
            docs.append(doc_cleaned)

            doc_chunks = self.chunker.chunk(doc_cleaned)
            chunks.extend(doc_chunks)

        save_chunks_jsonl(chunks, output_path / "chunks.jsonl")
        report = self.monitor.audit(docs, chunks, self.strategy_name)
        save_audit_report(report, report_path)

        logger.info(
            "pipeline_complete",
            docs=len(docs),
            chunks=len(chunks),
            coverage=report.metrics.char_coverage_ratio,
            status=report.metrics.status,
        )
        return report
