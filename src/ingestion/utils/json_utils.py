"""JSON serialization and report output utilities."""

from pathlib import Path

from ingestion.exporters import export_audit_report, export_chunks_jsonl
from ingestion.models import AuditReport, Chunk


def save_chunks_jsonl(chunks: list[Chunk], output_file: str | Path) -> None:
    """Serialize chunks to JSON Lines format."""
    export_chunks_jsonl(chunks, output_file)


def save_audit_report(report: AuditReport, report_file: str | Path) -> None:
    """Serialize audit report to formatted JSON."""
    export_audit_report(report, report_file)

