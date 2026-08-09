"""Ingestion pipeline package."""

from ingestion.chunkers import (
    BaseChunker,
    ChunkingStrategy,
    FixedSizeChunker,
    RecursiveStructuralChunker,
)
from ingestion.cleaner import TextCleaner
from ingestion.console import RichConsoleRenderer
from ingestion.detector import OrphanBlockDetector, StructuralBlock
from ingestion.exceptions import (
    AuditError,
    ChunkError,
    CleanError,
    DocumentLoadError,
    IngestionError,
)
from ingestion.exporters import (
    AuditReportExporter,
    BaseExporter,
    JSONLChunkExporter,
    export_audit_report,
    export_chunks_jsonl,
)
from ingestion.file_shield import FileShieldContext, IngestionStage, StageError
from ingestion.gatekeeper import ExitCodeGatekeeper
from ingestion.loaders import (
    DocumentLoader,
    MarkdownLoader,
    TextLoader,
    TextMarkdownLoader,
    compute_document_id,
    get_loader,
)
from ingestion.models import (
    AuditReport,
    BaseDomainModel,
    Chunk,
    Document,
    DocumentReport,
    IngestionConfig,
    IngestionMetrics,
    IngestionReport,
    LoadedDocument,
    StrategyType,
    TokenizerType,
)
from ingestion.pipeline import IngestionPipeline, PipelineOrchestrator, PipelineResult
from ingestion.tokenizers import (
    BaseTokenizer,
    GeminiEncoder,
    HeuristicTokenizer,
    TiktokenEncoder,
    get_tokenizer,
)

__all__ = [
    "BaseDomainModel",
    "StrategyType",
    "TokenizerType",
    "IngestionConfig",
    "LoadedDocument",
    "Document",
    "Chunk",
    "DocumentReport",
    "IngestionMetrics",
    "IngestionReport",
    "AuditReport",
    "IngestionError",
    "DocumentLoadError",
    "CleanError",
    "ChunkError",
    "AuditError",
    "IngestionStage",
    "StageError",
    "FileShieldContext",
    "DocumentLoader",
    "TextLoader",
    "MarkdownLoader",
    "TextMarkdownLoader",
    "get_loader",
    "compute_document_id",
    "TextCleaner",
    "BaseTokenizer",
    "TiktokenEncoder",
    "GeminiEncoder",
    "HeuristicTokenizer",
    "get_tokenizer",
    "ChunkingStrategy",
    "BaseChunker",
    "FixedSizeChunker",
    "RecursiveStructuralChunker",
    "OrphanBlockDetector",
    "StructuralBlock",
    "BaseExporter",
    "JSONLChunkExporter",
    "AuditReportExporter",
    "export_chunks_jsonl",
    "export_audit_report",
    "PipelineOrchestrator",
    "PipelineResult",
    "IngestionPipeline",
    "RichConsoleRenderer",
    "ExitCodeGatekeeper",
]



