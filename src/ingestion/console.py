"""Rich terminal UI renderer for RAG document ingestion pipeline."""

from collections.abc import Sequence
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ingestion.models import AuditReport, DocumentReport, IngestionReport
from ingestion.pipeline import PipelineResult


class RichConsoleRenderer:
    """Formatter rendering rich console status tables and panels."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def render_header(self, strategy: str, input_dir: str | Path) -> Panel:
        """Build launch status panel header."""
        return Panel.fit(
            f"[bold blue]RAG Ingestion Pipeline Engine[/bold blue]\n"
            f"Strategy: [cyan]{strategy}[/cyan] | Input: [yellow]{input_dir}[/yellow]",
            title="⚡ Ingestion Pipeline Launch",
        )

    def render_document_table(self, doc_reports: Sequence[DocumentReport]) -> Table:
        """Build per-file audit metrics status table."""
        table = Table(title="📄 Per-File Audit Breakdown", expand=True)
        table.add_column("Document", style="cyan", no_wrap=True)
        table.add_column("Chunks", justify="right", style="magenta")
        table.add_column("Coverage", justify="right")
        table.add_column("Orphan Blocks", justify="right")
        table.add_column("Token Delta", justify="right")
        table.add_column("Status", justify="center")

        for r in doc_reports:
            fname = Path(r.source_path).name or r.document_id
            cov_pct = r.char_coverage_ratio * 100
            cov_style = (
                "green" if cov_pct >= 98 else ("yellow" if cov_pct >= 90 else "red")
            )
            cov_str = f"[{cov_style}]{cov_pct:.1f}%[/{cov_style}]"

            orph_str = (
                "[green]0[/green]"
                if r.orphan_blocks == 0
                else f"[bold red]{r.orphan_blocks}[/bold red]"
            )

            delta_val = r.token_count_delta
            delta_str = (
                "[dim]0[/dim]"
                if delta_val == 0
                else (
                    f"[yellow]+{delta_val}[/yellow]"
                    if delta_val > 0
                    else f"[cyan]{delta_val}[/cyan]"
                )
            )

            status_str = (
                "[bold green]OK[/bold green]"
                if r.status.lower() in ("ok", "passed")
                else (
                    "[bold yellow]WARN[/bold yellow]"
                    if r.status.lower() == "warning"
                    else "[bold red]ERROR[/bold red]"
                )
            )

            table.add_row(
                fname,
                str(r.chunk_count),
                cov_str,
                orph_str,
                delta_str,
                status_str,
            )
        return table

    def render_summary_table(
        self,
        audit_report: AuditReport,
        ingestion_report: IngestionReport | None = None,
    ) -> Table:
        """Build overall aggregate audit metrics table."""
        m = audit_report.metrics
        table = Table(title="📈 Ingestion Audit Results Summary")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        table.add_row("Total Input Docs", str(m.total_docs))
        table.add_row("Total Output Chunks", str(m.total_chunks))
        table.add_row("Coverage Ratio", f"{m.char_coverage_ratio * 100:.2f}%")
        table.add_row(
            "Orphan Block Count",
            "[green]0[/green]"
            if m.orphan_block_count == 0
            else f"[bold red]{m.orphan_block_count}[/bold red]",
        )

        if ingestion_report:
            table.add_row(
                "Documents in Error",
                "[green]0[/green]"
                if ingestion_report.documents_in_error == 0
                else f"[bold red]{ingestion_report.documents_in_error}[/bold red]",
            )

        status_fmt = (
            "[bold green]PASSED[/bold green]"
            if m.status == "PASSED"
            else "[bold red]FAILED[/bold red]"
        )
        table.add_row("Audit Status", status_fmt)
        return table

    def render_pipeline_result(self, result: PipelineResult) -> None:
        """Render complete rich output suite to console."""
        self.console.print(self.render_document_table(result.doc_reports))
        self.console.print(
            self.render_summary_table(result.audit_report, result.ingestion_report)
        )
