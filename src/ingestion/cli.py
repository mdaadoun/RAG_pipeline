"""Typer CLI entrypoint for RAG document ingestion pipeline with Rich UI."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from config.logging import setup_logging
from config.settings import get_settings
from ingestion.benchmark import StrategyBenchmarkRunner
from ingestion.console import RichConsoleRenderer
from ingestion.exceptions import IngestionError
from ingestion.gatekeeper import ExitCodeGatekeeper
from ingestion.models import IngestionConfig, StrategyType
from ingestion.pipeline import PipelineOrchestrator
from ingestion.quality_gate import QualityGateRunner

app = typer.Typer(
    name="ingest",
    help="RAG Ingestion Pipeline & Quality Audit CLI Engine",
    add_completion=False,
)
console = Console()


def _execute_run(
    input_dir: Path,
    output_dir: Path,
    strategy: str,
    chunk_size: int,
    overlap: int,
    min_chunk_size: int,
    report: Path,
) -> None:
    """Execute end-to-end ingestion pipeline."""
    setup_logging(get_settings().log_level)
    if strategy not in [s.value for s in StrategyType]:
        raise IngestionError(f"Invalid strategy '{strategy}'. Valid choices: fixed, recursive")

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
    result = orchestrator.run(input_dir=input_dir, output_dir=output_dir, report_path=report)
    renderer.render_pipeline_result(result)

    gatekeeper = ExitCodeGatekeeper(coverage_threshold=config.coverage_threshold)
    if gatekeeper.should_exit(result):
        console.print("[bold red]CRITICAL: Quality gates failed![/bold red]")
        for reason in gatekeeper.get_blocking_reasons(result):
            console.print(f"[bold red] - {reason}[/bold red]")
        raise typer.Exit(code=gatekeeper.evaluate(result))


def _execute_benchmark(input_dir: Path | None, chunk_size: int, overlap: int) -> None:
    """Execute comparative benchmark."""
    runner = StrategyBenchmarkRunner()
    result = runner.run_benchmark(input_dir=input_dir, chunk_size=chunk_size, overlap=overlap)
    console.print("\n[bold cyan]=== Comparative Strategy Benchmark Results ===[/bold cyan]\n")
    console.print(runner.format_markdown_table(result))
    console.print(
        f"\n[bold green]Recommended Strategy:[/bold green] {result.winning_strategy.value.upper()}"
    )
    for note in result.summary_notes:
        console.print(f" • {note}")


def _execute_verify(report_path: Path) -> None:
    """Execute quality gates & final delivery verification."""
    runner = QualityGateRunner()
    res = runner.evaluate_all(report_path)
    console.print("\n[bold cyan]=== Quality Gates & Final Delivery Verification ===[/bold cyan]")
    console.print(f"Mypy Strict Check: {'PASSED' if res.mypy_passed else 'FAILED'}")
    console.print(f"Ruff Lint Check: {'PASSED' if res.ruff_passed else 'FAILED'}")
    console.print(f"Pytest Test Suite: {'PASSED' if res.pytest_passed else 'FAILED'}")
    console.print(f"Coverage Ratio: {res.coverage_ratio:.2%}")
    console.print(f"Deliverable Verification: {'PASSED' if res.report_verified else 'FAILED'}")
    if res.all_passed:
        console.print("[bold green]\nStatus: ALL QUALITY GATES PASSED (RELEASE READY)[/bold green]")
    else:
        console.print("[bold red]\nStatus: QUALITY GATES FAILED[/bold red]")
        for detail in res.details:
            console.print(f"[red] - {detail}[/red]")
        raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    input_dir: Annotated[Path, typer.Option("--input", "-i", help="Input directory")] = Path("./data/input"),
    output_dir: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path("./data/output"),
    strategy: Annotated[str, typer.Option("--strategy", "-s", help="Chunking strategy")] = "recursive",
    chunk_size: Annotated[int, typer.Option("--chunk-size", "-c", help="Chunk size")] = 512,
    overlap: Annotated[int, typer.Option("--overlap", help="Overlap size")] = 64,
    min_chunk_size: Annotated[int, typer.Option("--min-chunk-size", help="Min chunk size")] = 50,
    report: Annotated[Path, typer.Option("--report", "-r", help="Audit report JSON path")] = Path("rapport_ingestion.json"),
    benchmark: Annotated[bool, typer.Option("--benchmark", "-b", help="Run benchmark")] = False,
    verify: Annotated[bool, typer.Option("--verify", "-v", help="Run quality gates verification")] = False,
) -> None:
    """RAG Ingestion Pipeline & Quality Audit CLI Engine."""
    if ctx.invoked_subcommand is not None:
        return
    try:
        if verify:
            _execute_verify(report_path=report)
        elif benchmark:
            _execute_benchmark(input_dir=input_dir, chunk_size=chunk_size, overlap=overlap)
        else:
            _execute_run(input_dir, output_dir, strategy, chunk_size, overlap, min_chunk_size, report)
    except typer.Exit:
        raise
    except IngestionError as err:
        console.print(f"[bold red]Ingestion Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err
    except Exception as err:
        console.print(f"[bold red]CLI Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err


@app.command()
def run(
    input_dir: Annotated[Path, typer.Option("--input", "-i")] = Path("./data/input"),
    output_dir: Annotated[Path, typer.Option("--output", "-o")] = Path("./data/output"),
    strategy: Annotated[str, typer.Option("--strategy", "-s")] = "recursive",
    chunk_size: Annotated[int, typer.Option("--chunk-size", "-c")] = 512,
    overlap: Annotated[int, typer.Option("--overlap")] = 64,
    min_chunk_size: Annotated[int, typer.Option("--min-chunk-size")] = 50,
    report: Annotated[Path, typer.Option("--report", "-r")] = Path("rapport_ingestion.json"),
) -> None:
    """Execute end-to-end ingestion pipeline."""
    _execute_run(input_dir, output_dir, strategy, chunk_size, overlap, min_chunk_size, report)


@app.command(name="benchmark")
def benchmark_cmd(
    input_dir: Annotated[Path | None, typer.Option("--input", "-i")] = None,
    chunk_size: Annotated[int, typer.Option("--chunk-size", "-c")] = 512,
    overlap: Annotated[int, typer.Option("--overlap")] = 64,
) -> None:
    """Run comparative benchmark."""
    _execute_benchmark(input_dir, chunk_size, overlap)


@app.command(name="verify")
def verify_cmd(
    report: Annotated[Path, typer.Option("--report", "-r")] = Path("rapport_ingestion.json"),
) -> None:
    """Verify code quality gates and final release deliverable."""
    _execute_verify(report_path=report)


if __name__ == "__main__":
    app()
