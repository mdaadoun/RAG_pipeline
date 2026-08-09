"""Typer CLI entrypoint for RAG document ingestion pipeline with Rich UI."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from config.logging import setup_logging
from config.settings import get_settings
from ingestion.console import RichConsoleRenderer
from ingestion.exceptions import IngestionError
from ingestion.gatekeeper import ExitCodeGatekeeper
from ingestion.models import IngestionConfig, StrategyType
from ingestion.pipeline import PipelineOrchestrator

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
            "--input",
            "-i",
            help="Directory containing source text/markdown documents",
        ),
    ] = Path("./data/input"),
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output directory for serialized JSONL chunks",
        ),
    ] = Path("./data/output"),
    strategy: Annotated[
        str,
        typer.Option(
            "--strategy",
            "-s",
            help="Chunking strategy: 'fixed' or 'recursive'",
        ),
    ] = "recursive",
    chunk_size: Annotated[
        int,
        typer.Option(
            "--chunk-size",
            "-c",
            help="Target chunk size in characters/tokens",
        ),
    ] = 512,
    overlap: Annotated[
        int,
        typer.Option(
            "--overlap",
            help="Overlap character size",
        ),
    ] = 64,
    min_chunk_size: Annotated[
        int,
        typer.Option(
            "--min-chunk-size",
            help="Minimum character threshold",
        ),
    ] = 50,
    report: Annotated[
        Path,
        typer.Option(
            "--report",
            "-r",
            help="Destination file path for global audit report JSON",
        ),
    ] = Path("rapport_ingestion.json"),
) -> None:
    """Execute end-to-end ingestion pipeline and evaluate quality metrics."""
    try:
        settings = get_settings()
        setup_logging(settings.log_level)

        if strategy not in [s.value for s in StrategyType]:
            raise IngestionError(
                f"Invalid strategy '{strategy}'. Valid choices: fixed, recursive"
            )

        renderer = RichConsoleRenderer(console)
        console.print(renderer.render_header(strategy, input_dir))

        config = IngestionConfig(
            strategy=StrategyType(strategy),
            chunk_size=chunk_size,
            overlap=overlap,
            min_chunk_size=min_chunk_size,
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            report_path=str(report),
        )

        orchestrator = PipelineOrchestrator(config)
        result = orchestrator.run(
            input_dir=input_dir,
            output_dir=output_dir,
            report_path=report,
        )

        renderer.render_pipeline_result(result)

        gatekeeper = ExitCodeGatekeeper(coverage_threshold=config.coverage_threshold)
        if gatekeeper.should_exit(result):
            console.print("[bold red]CRITICAL: Quality gates failed![/bold red]")
            for reason in gatekeeper.get_blocking_reasons(result):
                console.print(f"[bold red] - {reason}[/bold red]")
            raise typer.Exit(code=gatekeeper.evaluate(result))

    except typer.Exit:
        raise
    except IngestionError as err:
        console.print(f"[bold red]Ingestion Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err
    except Exception as err:
        console.print(f"[bold red]Unexpected Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err


if __name__ == "__main__":
    app()

