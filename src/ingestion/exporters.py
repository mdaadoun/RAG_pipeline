"""JSONL and Audit Report exporters for RAG ingestion pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Generic, TypeVar

from ingestion.exceptions import AuditError
from ingestion.models import AuditReport, BaseDomainModel, Chunk, IngestionReport

T = TypeVar("T", bound=Any)


class BaseExporter(ABC, Generic[T]):
    """Abstract base class for serialization exporters."""

    @abstractmethod
    def export(self, data: T, output_path: str | Path) -> Path:
        """Export data object to target file path."""
        ...


class JSONLChunkExporter(BaseExporter[list[Chunk]]):
    """Exporter for serializing Chunk domain models to JSON Lines format."""

    def export(self, data: list[Chunk], output_path: str | Path) -> Path:
        """Serialize list of Chunk domain models to a JSONL file."""
        return self.export_stream(data, output_path)

    def export_stream(self, chunks: Iterable[Chunk], output_path: str | Path) -> Path:
        """Stream chunks into JSON Lines file line-by-line."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("w", encoding="utf-8") as f:
                for chunk in chunks:
                    f.write(chunk.model_dump_json(by_alias=True) + "\n")
            return path
        except Exception as exc:
            raise AuditError(f"Failed to export chunks to JSONL: {exc}") from exc

    def read(self, input_path: str | Path) -> list[Chunk]:
        """Read and validate JSONL file back into Chunk domain models."""
        path = Path(input_path)
        if not path.is_file():
            raise AuditError(f"JSONL chunk file not found: {path}")
        chunks: list[Chunk] = []
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        chunks.append(Chunk.model_validate_json(stripped))
            return chunks
        except Exception as exc:
            raise AuditError(f"Failed to parse JSONL chunks from {path}: {exc}") from exc


class AuditReportExporter(BaseExporter[BaseDomainModel]):
    """Exporter for serializing audit & ingestion reports to formatted JSON."""

    def export(
        self,
        data: BaseDomainModel,
        output_path: str | Path,
        indent: int = 2,
    ) -> Path:
        """Serialize AuditReport or IngestionReport to formatted JSON file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            json_str = data.model_dump_json(indent=indent)
            path.write_text(json_str, encoding="utf-8")
            return path
        except Exception as exc:
            raise AuditError(f"Failed to export audit report to {path}: {exc}") from exc

    def read_audit_report(self, input_path: str | Path) -> AuditReport:
        """Parse JSON file back into AuditReport domain model."""
        path = Path(input_path)
        if not path.is_file():
            raise AuditError(f"Audit report file not found: {path}")
        try:
            return AuditReport.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise AuditError(f"Failed to parse AuditReport from {path}: {exc}") from exc

    def read_ingestion_report(self, input_path: str | Path) -> IngestionReport:
        """Parse JSON file back into IngestionReport domain model."""
        path = Path(input_path)
        if not path.is_file():
            raise AuditError(f"Ingestion report file not found: {path}")
        try:
            return IngestionReport.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise AuditError(f"Failed to parse IngestionReport from {path}: {exc}") from exc


def export_chunks_jsonl(chunks: list[Chunk], output_path: str | Path) -> Path:
    """Procedural helper exporting chunks to JSONL format."""
    return JSONLChunkExporter().export(chunks, output_path)


def export_audit_report(
    report: BaseDomainModel,
    output_path: str | Path,
) -> Path:
    """Procedural helper exporting audit or ingestion report to formatted JSON."""
    return AuditReportExporter().export(report, output_path)
