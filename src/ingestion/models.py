"""Immutable Pydantic V2 domain models for RAG document ingestion & audit."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseDomainModel(BaseModel):
    """Base immutable Pydantic domain model forbidding extra fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class StrategyType(str, Enum):
    """Supported document chunking strategies."""

    FIXED = "fixed"
    RECURSIVE = "recursive"


class TokenizerType(str, Enum):
    """Supported model-agnostic tokenizer providers."""

    GEMINI = "gemini"
    TIKTOKEN = "tiktoken"
    HEURISTIC = "heuristic"


class IngestionConfig(BaseDomainModel):
    """Configuration model for document ingestion & chunking parameters."""

    strategy: StrategyType = Field(default=StrategyType.RECURSIVE, description="Chunking strategy type")
    tokenizer: TokenizerType = Field(default=TokenizerType.GEMINI, description="Tokenizer provider type")
    chunk_size: int = Field(default=512, gt=0, description="Target character size per chunk")
    overlap: int = Field(default=64, ge=0, description="Character overlap between consecutive chunks")
    min_chunk_size: int = Field(default=50, ge=0, description="Minimum acceptable chunk character size")
    coverage_threshold: float = Field(
        default=0.98, ge=0.0, le=1.0, description="Minimum character coverage audit threshold"
    )
    input_dir: str = Field(default="data/input", description="Input directory path for source documents")
    output_dir: str = Field(default="data/output", description="Output directory path for chunk artifacts")
    report_path: str = Field(default="rapport_ingestion.json", description="Path for generating audit JSON report")



class LoadedDocument(BaseDomainModel):
    """Domain model representing a loaded raw source document."""

    id: str = Field(..., description="Unique document identifier")
    file_path: str = Field(..., description="Absolute or relative file path")
    content: str = Field(..., description="Raw text content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata key-values")

    @property
    def char_count(self) -> int:
        """Calculate total character length."""
        return len(self.content)

    @property
    def token_count(self) -> int:
        """Estimate token count based on whitespace word splits."""
        return len(self.content.split())


# Alias for backward compatibility
Document = LoadedDocument


class Chunk(BaseDomainModel):
    """Domain model representing a sliced document text chunk."""

    id: str = Field(..., description="Unique chunk identifier")
    doc_id: str = Field(..., description="Parent document identifier")
    chunk_index: int = Field(default=0, description="Zero-based index sequence")
    content: str = Field(..., description="Chunk text content")
    start_char: int = Field(..., description="Start character offset in parent document")
    end_char: int = Field(..., description="End character offset in parent document")
    token_count: int = Field(..., description="Token count in chunk")
    is_orphan_block: bool = Field(default=False, description="Flag for orphaned table/code blocks")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")

    @property
    def document_id(self) -> str:
        """Alias property for doc_id."""
        return self.doc_id

    @property
    def char_count(self) -> int:
        """Calculate total character length of chunk content."""
        return len(self.content)



class DocumentReport(BaseDomainModel):
    """Per-document structural audit report model."""

    document_id: str = Field(..., description="Document identifier")
    source_path: str = Field(..., description="Source file path")
    char_coverage_ratio: float = Field(default=1.0, description="Character coverage ratio")
    duplicate_char_ratio: float = Field(default=0.0, description="Duplicate character ratio")
    orphan_blocks: int = Field(default=0, description="Count of orphan blocks")
    token_count_delta: int = Field(default=0, description="Token count delta")
    undersized_chunks_ratio: float = Field(default=0.0, description="Undersized chunks ratio")
    chunk_count: int = Field(default=0, description="Total chunks for document")
    status: str = Field(default="ok", description="Status: ok, warning, or error")
    errors: list[str] = Field(default_factory=list, description="List of error messages")


class IngestionMetrics(BaseDomainModel):
    """Aggregate statistical quality and coverage audit metrics."""

    total_docs: int = Field(..., description="Total input documents processed")
    total_chunks: int = Field(..., description="Total output chunks generated")
    total_original_chars: int = Field(..., description="Sum of raw source document characters")
    total_chunk_chars: int = Field(..., description="Sum of chunk content characters")
    char_coverage_ratio: float = Field(..., description="Character retention ratio (0.0 to 1.0)")
    duplicate_char_ratio: float = Field(..., description="Ratio of duplicate characters across overlaps")
    orphan_block_count: int = Field(..., description="Total fragmented table/code blocks detected")
    status: str = Field(..., description="Pipeline execution status: PASSED or FAILED")


class IngestionReport(BaseDomainModel):
    """Global structured ingestion report deliverable."""

    corpus_path: str = Field(..., description="Input corpus path")
    strategy_used: str = Field(..., description="Chunking strategy applied")
    execution_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="UTC execution timestamp"
    )
    documents: list[DocumentReport] = Field(default_factory=list, description="Per-document audit reports")
    total_chunks: int = Field(default=0, description="Total chunks generated across corpus")
    global_char_coverage_ratio: float = Field(default=1.0, description="Global character coverage ratio")
    documents_in_error: int = Field(default=0, description="Count of documents with errors")
    has_blocking_alerts: bool = Field(default=False, description="Flag indicating blocking quality alerts")


class AuditReport(BaseDomainModel):
    """Global structured ingestion report deliverable (legacy audit metrics)."""

    timestamp: str = Field(..., description="ISO 8601 execution timestamp")
    strategy_used: str = Field(..., description="Chunking strategy applied")
    metrics: IngestionMetrics = Field(..., description="Calculated aggregate audit metrics")
    document_ids: list[str] = Field(default_factory=list, description="Processed document list")
    errors: list[str] = Field(default_factory=list, description="Encountered warning/error messages")
