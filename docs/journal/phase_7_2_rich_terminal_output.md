# Session 7.2: Rich Terminal Output
**Date:** 2026-08-09

Implemented Rich console status tables in `src/ingestion/console.py` (`RichConsoleRenderer`) and integrated it into `src/ingestion/cli.py`. Provides per-document status breakdown tables displaying character coverage ratios, orphan block counts, token count deltas, document statuses, aggregate summary tables, dynamic threshold color styling (green, yellow, red), and comprehensive unit testing.

---

### 1. 🎓 Concepts Introduced
- **Rich Console Renderer:** A dedicated presentation component leveraging the Rich library (`rich.console.Console`, `rich.panel.Panel`, `rich.table.Table`) to format structured domain reports into visually rich status tables and panels.
- **Per-Document Breakdown Table:** A tabular terminal visualizer detailing per-file document coverage, chunk counts, orphan block counts, token deltas, and status indicators.
- **Conditional Style Formatting:** Dynamic terminal text styling where cell colors (green, yellow, red) automatically adapt based on threshold bounds of metrics like character coverage or orphan counts.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Decoupled Console Renderer Class]
- **Option 1:** Embed inline table construction directly inside `cli.py`.
- **Option 2 (Selected):** Implement `RichConsoleRenderer` in `src/ingestion/console.py`. Adheres to presentation layer isolation and Single Responsibility Principle, enabling independent unit testing of renderables without launching Typer CLI commands.

#### [ADR-02: Per-Document Breakdown & Summary Dual-Table Layout]
- **Option 1:** Display only a single global metric summary table.
- **Option 2 (Selected):** Render both a granular per-file breakdown table (`📄 Per-File Audit Breakdown`) and an aggregate summary table (`📈 Ingestion Audit Results Summary`). Grants real-time visibility into specific failing files across large document corpora.

#### [ADR-03: Threshold-Based Color Coding Rules]
- **Option 1:** Use uniform text colors for all metric cells regardless of metric values.
- **Option 2 (Selected):** Apply color rules: character coverage ratio $\ge 98\%$ styled green, $90-97\%$ yellow, $<90\%$ red; orphan counts of $0$ styled green, $>0$ styled bold red; statuses `OK` styled green, `WARN` yellow, `ERROR` red.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/console.py
class RichConsoleRenderer:
    """Formatter rendering rich console status tables and panels."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def render_header(self, strategy: str, input_dir: str | Path) -> Panel:
        return Panel.fit(
            f"[bold blue]RAG Ingestion Pipeline Engine[/bold blue]\n"
            f"Strategy: [cyan]{strategy}[/cyan] | Input: [yellow]{input_dir}[/yellow]",
            title="⚡ Ingestion Pipeline Launch",
        )

    def render_document_table(self, doc_reports: Sequence[DocumentReport]) -> Table:
        table = Table(title="📄 Per-File Audit Breakdown", expand=True)
        # Adds Document, Chunks, Coverage, Orphan Blocks, Token Delta, Status columns with color styling
        ...
        return table

    def render_pipeline_result(self, result: PipelineResult) -> None:
        self.console.print(self.render_document_table(result.doc_reports))
        self.console.print(self.render_summary_table(result.audit_report, result.ingestion_report))
```

```bash
# Verification suite execution
.venv/bin/pytest tests/unit/test_console.py tests/unit/test_cli.py -v
# Result: 9 passed in 0.08s
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Rich Console Renderer Module:** Implemented `RichConsoleRenderer` in `src/ingestion/console.py` providing `render_header()`, `render_document_table()`, `render_summary_table()`, and `render_pipeline_result()`.
2. [x] **Per-Document Breakdown Table:** Added per-file tabular output displaying source path/filename, chunk count, coverage percentage, orphan blocks, token delta, and status.
3. [x] **Conditional Style Formatting:** Implemented green/yellow/red color rules for coverage thresholds, orphan count alerts, token deltas, and document status badges.
4. [x] **CLI Pipeline Integration:** Updated `src/ingestion/cli.py` to run `PipelineOrchestrator` and output rich status tables via `RichConsoleRenderer`.
5. [x] **Unit Testing:** Created `tests/unit/test_console.py` validating header panels, document breakdown tables, summary tables, and captured console text output.
6. [x] **Quality Assurance:** Verified 100% compliance with `mypy` strict typing, `ruff check`, and full pytest suite (122 passed).
