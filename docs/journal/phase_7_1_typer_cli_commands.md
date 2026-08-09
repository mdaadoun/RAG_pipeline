# Session 7.1: Typer CLI Commands
**Date:** 2026-08-09

Implemented standard Typer CLI commands in `src/ingestion/cli.py` featuring declarative CLI option parameters (`--input`, `--output`, `--strategy`, `--chunk-size`, `--overlap`, `--min-chunk-size`, `--report`), Rich UI status rendering, strategy Enum pre-validation, exception shielding, and exit code quality gating.

---

### 1. 🎓 Concepts Introduced
- **Typer CLI Framework:** A modern, strongly typed Python CLI framework leveraging Pydantic and type annotations to provide automatic flag parsing, validation, and auto-generated `--help` documentation.
- **Annotated CLI Parameters:** Usage of `typing.Annotated` with `typer.Option` to declare option flags (`-i`, `--input`), default values, and parameter documentation inline within command function signatures.
- **Rich Terminal UI Integration:** Rendering launch status panels and tabular audit summaries (`rich.panel.Panel`, `rich.table.Table`) for human-readable feedback during batch pipeline execution.
- **Quality Gate Exit Gating:** Explicit emission of non-zero exit code (`code=1`) when quality audit status evaluates to `FAILED` or execution exceptions occur, enabling CI/CD pipeline breakage.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Typer Framework with Annotated Type Hints]
- **Option 1:** Use low-level `argparse` or legacy `click` decorators.
- **Option 2 (Selected):** Use `typer.Typer` with `typing.Annotated` type hints. Ensures strict typing compatibility with MyPy (`--strict`), simplifies parameter maintenance, and auto-generates structured CLI documentation.

#### [ADR-02: Rich Terminal Output & Audit Summary Table]
- **Option 1:** Plain text `print()` statements or basic log lines.
- **Option 2 (Selected):** Integrate `rich.console.Console`, `Panel`, and `Table` to present high-visibility visual feedback, displaying total input docs, total output chunks, coverage ratio, orphan block counts, and audit status.

#### [ADR-03: Strategy Enum Pre-validation Gate]
- **Option 1:** Pass raw CLI strategy strings directly into pipeline execution and allow downstream components to fail.
- **Option 2 (Selected):** Validate `--strategy` input against `StrategyType` enum values (`fixed`, `recursive`) at the CLI boundary, raising an explicit `IngestionError` for invalid strategies.

#### [ADR-04: CLI Exception Shielding & Non-Zero Exit Codes]
- **Option 1:** Allow unhandled Python tracebacks to dump to stdout on errors.
- **Option 2 (Selected):** Wrap execution in top-level `try/except` catching `IngestionError` and general exceptions, displaying formatted red error messages via Rich, and cleanly exiting via `raise typer.Exit(code=1)`.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/cli.py
@app.command()
def run(
    input_dir: Annotated[Path, typer.Option("--input", "-i", help="Source documents dir")] = Path("./data/input"),
    output_dir: Annotated[Path, typer.Option("--output", "-o", help="Serialized JSONL output dir")] = Path("./data/output"),
    strategy: Annotated[str, typer.Option("--strategy", "-s", help="Chunking strategy: 'fixed' or 'recursive'")] = "recursive",
    chunk_size: Annotated[int, typer.Option("--chunk-size", "-c", help="Target chunk size")] = 512,
    overlap: Annotated[int, typer.Option("--overlap", help="Overlap character size")] = 64,
    min_chunk_size: Annotated[int, typer.Option("--min-chunk-size", help="Minimum character threshold")] = 50,
    report: Annotated[Path, typer.Option("--report", "-r", help="Audit report JSON output path")] = Path("rapport_ingestion.json"),
) -> None:
    try:
        if strategy not in [s.value for s in StrategyType]:
            raise IngestionError(f"Invalid strategy '{strategy}'. Valid choices: fixed, recursive")
        
        pipeline = IngestionPipeline(strategy_name=strategy, chunk_size=chunk_size, overlap=overlap, min_chunk_size=min_chunk_size)
        audit_report = pipeline.run(input_dir=input_dir, output_dir=output_dir, report_path=report)
        
        # Render Rich audit table
        if audit_report.metrics.status != "PASSED":
            raise typer.Exit(code=1)
    except IngestionError as err:
        console.print(f"[bold red]Ingestion Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err
```

```bash
# Verification suite execution
.venv/bin/pytest tests/unit/test_cli.py -v
# Result: 5 passed in 0.05s
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Typer CLI Command Entrypoint:** Implemented `run` command in `src/ingestion/cli.py` with full CLI options (`--input`, `--output`, `--strategy`, `--chunk-size`, `--overlap`, `--min-chunk-size`, `--report`).
2. [x] **Strategy Pre-Validation:** Added explicit validation against `StrategyType` enum before launching pipeline orchestrator.
3. [x] **Rich UI Integration:** Displayed launch panel and tabular summary of audit metrics (Total Docs, Output Chunks, Coverage Ratio, Orphan Count, Audit Status).
4. [x] **Exception Shielding & Exit Code Gating:** Ensured domain `IngestionError` and audit failures raise `typer.Exit(code=1)`.
5. [x] **Unit Testing:** Created `tests/unit/test_cli.py` testing `--help`, default and custom option runs, invalid strategies, and empty directory handling using `typer.testing.CliRunner`.
6. [x] **Code Quality:** Verified 100% compliance with `mypy --explicit-package-bases` and `ruff check`.
