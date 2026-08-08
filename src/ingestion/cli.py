"""Typer CLI entrypoint for RAG document ingestion pipeline with Rich UI."""

from pathlib import Path
from typing import Annotated

import typer
from ingestion.pipeline import IngestionPipeline
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.logging import setup_logging
from config.settings import get_settings

app = typer.Typer(
    name="ingest",
    help="RAG Ingestion Pipeline & Quality Audit CLI Engine",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    input_dir: Annotated[
        Path,
        typer.Option(
            "--input", "-i", help="Directory containing source text/markdown documents"
        ),
    ] = Path("./data/input"),
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output", "-o", help="Output directory for serialized JSONL chunks"
        ),
    ] = Path("./data/output"),
    strategy: Annotated[
        str,
        typer.Option(
            "--strategy", "-s", help="Chunking strategy: 'fixed' or 'recursive'"
        ),
    ] = "recursive",
    chunk_size: Annotated[
        int,
        typer.Option(
            "--chunk-size", "-c", help="Target chunk size in characters/tokens"
        ),
    ] = 512,
    overlap: Annotated[
        int, typer.Option("--overlap", help="Overlap character size")
    ] = 64,
    min_chunk_size: Annotated[
        int, typer.Option("--min-chunk-size", help="Minimum character threshold")
    ] = 50,
    report: Annotated[
        Path,
        typer.Option(
            "--report", "-r", help="Destination file path for global audit report JSON"
        ),
    ] = Path("rapport_ingestion.json"),
) -> None:
    """Execute end-to-end ingestion pipeline and evaluate quality metrics."""
    settings = get_settings()
    setup_logging(settings.log_level)

    console.print(
        Panel.fit(
            f"[bold blue]RAG Ingestion Pipeline Engine[/bold blue]\n"
            f"Strategy: [cyan]{strategy}[/cyan] | Input: [yellow]{input_dir}[/yellow]",
            title="⚡ Ingestion Pipeline Launch",
        )
    )

    pipeline = IngestionPipeline(
        strategy_name=strategy,
        chunk_size=chunk_size,
        overlap=overlap,
        min_chunk_size=min_chunk_size,
    )

    audit_report = pipeline.run(
        input_dir=input_dir,
        output_dir=output_dir,
        report_path=report,
    )

    m = audit_report.metrics
    table = Table(title="📈 Ingestion Audit Results Summary")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Total Input Docs", str(m.total_docs))
    table.add_row("Total Output Chunks", str(m.total_chunks))
    table.add_row("Coverage Ratio", f"{m.char_coverage_ratio * 100:.2f}%")
    table.add_row("Orphan Block Count", str(m.orphan_block_count))
    table.add_row(
        "Audit Status",
        "[bold green]PASSED[/bold green]"
        if m.status == "PASSED"
        else "[bold red]FAILED[/bold red]",
    )

    console.print(table)

    if m.status != "PASSED":
        console.print("[bold red]CRITICAL: Quality gates failed![/bold red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
