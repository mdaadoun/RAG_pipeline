"""JSON serialization and report output utilities."""

import json
from pathlib import Path

from ingestion.models import AuditReport, Chunk


def save_chunks_jsonl(chunks: list[Chunk], output_file: str | Path) -> None:
    """Serialize chunks to JSON Lines format."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk.model_dump(), ensure_ascii=False) + "\n")


def save_audit_report(report: AuditReport, report_file: str | Path) -> None:
    """Serialize audit report to formatted JSON."""
    path = Path(report_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)
