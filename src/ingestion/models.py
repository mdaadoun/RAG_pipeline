"""Immutable Pydantic V2 domain models for RAG document ingestion & audit."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    """Domain representation of an ingested raw source document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

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


class Chunk(BaseModel):
    """Domain representation of a sliced document text chunk."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., description="Unique chunk identifier")
    doc_id: str = Field(..., description="Parent document identifier")
    chunk_index: int = Field(..., description="Zero-based index sequence")
    content: str = Field(..., description="Chunk text content")
    start_char: int = Field(..., description="Start character offset in parent document")
    end_char: int = Field(..., description="End character offset in parent document")
    token_count: int = Field(..., description="Token count in chunk")
    is_orphan_block: bool = Field(default=False, description="Flag for orphaned table/code blocks")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class IngestionMetrics(BaseModel):
    """Aggregate statistical quality and coverage audit metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_docs: int = Field(..., description="Total input documents processed")
    total_chunks: int = Field(..., description="Total output chunks generated")
    total_original_chars: int = Field(..., description="Sum of raw source document characters")
    total_chunk_chars: int = Field(..., description="Sum of chunk content characters")
    char_coverage_ratio: float = Field(..., description="Character retention ratio (0.0 to 1.0)")
    duplicate_char_ratio: float = Field(..., description="Ratio of duplicate characters across overlaps")
    orphan_block_count: int = Field(..., description="Total fragmented table/code blocks detected")
    status: str = Field(..., description="Pipeline execution status: PASSED or FAILED")


class AuditReport(BaseModel):
    """Global structured ingestion report deliverable."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: str = Field(..., description="ISO 8601 execution timestamp")
    strategy_used: str = Field(..., description="Chunking strategy applied")
    metrics: IngestionMetrics = Field(..., description="Calculated aggregate audit metrics")
    document_ids: list[str] = Field(default_factory=list, description="Processed document list")
    errors: list[str] = Field(default_factory=list, description="Encountered warning/error messages")
