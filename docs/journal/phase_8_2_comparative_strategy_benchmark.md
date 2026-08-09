# Session 8.2: Comparative Strategy Benchmark
**Date:** 2026-08-09

Implemented Comparative Strategy Benchmark engine in `src/ingestion/benchmark.py` (`StrategyBenchmarkRunner`, `BenchmarkStrategyMetrics`, `BenchmarkComparisonResult`) and CLI subcommand `ingest benchmark`. Enables empirical comparison of `FixedSizeChunker` vs `RecursiveStructuralChunker` over synthetic test corpus, contrasting character coverage, execution latency, token drift, and structural orphan block reduction.

---

### 1. 🎓 Concepts Introduced
- **Comparative Strategy Benchmark:** An empirical evaluation framework contrasting performance, character coverage, token delta, and structural orphan metrics across multiple chunking strategies.
- **Winning Strategy Selection:** Automated decision logic designating the optimal chunking strategy based on quality gate pass/fail status, zero orphan blocks, and superior character coverage.
- **Coverage Delta:** Mathematical difference in global character coverage ratio between recursive structural chunking and fixed-size chunking strategies.
- **Orphan Block Reduction:** The net decrease in fragmented structural elements (tables and code blocks) achieved when moving from fixed to recursive structural chunking.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Dual Pipeline Empirical Execution]
- **Option 1:** Mock metric projections or simulate chunking behavior.
- **Option 2 (Selected):** Execute actual `PipelineOrchestrator` runs over synthetic test corpus for both Fixed and Recursive chunking strategies. Empirical runtime data guarantees authentic timing measurements, accurate orphan block detection, character coverage ratios, and true exit code validation under real operational conditions.

#### [ADR-02: Pydantic Domain Models for Benchmark Outcomes]
- **Option 1:** Unstructured dictionary returns for benchmark metrics.
- **Option 2 (Selected):** Encapsulate strategy metrics and comparative deltas in immutable Pydantic V2 schemas (`BenchmarkStrategyMetrics`, `BenchmarkComparisonResult`). Ensures strict typing, schema immutability (`frozen=True`), extra field rejection (`extra="forbid"`), and seamless serialization into JSON report artifacts or Rich/Markdown representations.

#### [ADR-03: Dual CLI Interface Pattern]
- **Option 1:** Dedicated separate script outside the CLI tool.
- **Option 2 (Selected):** Expose subcommand `ingest benchmark` alongside main callback and `--benchmark` flag in `src/ingestion/cli.py`. Allows automated CI workflows and developers to invoke comparative benchmarking on demand with custom chunk size and input directory options without breaking existing CLI invocations.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/benchmark.py
class BenchmarkStrategyMetrics(BaseDomainModel):
    strategy: StrategyType
    execution_time_ms: float
    total_documents: int
    total_chunks: int
    avg_chunk_tokens: float
    avg_chunk_chars: float
    char_coverage_ratio: float
    duplicate_char_ratio: float
    orphan_blocks: int
    token_count_delta: int
    blocking_alerts: int
    status: str

class BenchmarkComparisonResult(BaseDomainModel):
    fixed_metrics: BenchmarkStrategyMetrics
    recursive_metrics: BenchmarkStrategyMetrics
    winning_strategy: StrategyType
    coverage_delta: float
    orphan_reduction: int
    chunk_count_diff: int
    summary_notes: list[str]

class StrategyBenchmarkRunner:
    def __init__(self, corpus: SyntheticCorpus | None = None) -> None: ...
    def run_benchmark(self, input_dir: str | Path | None = None, chunk_size: int = 512, overlap: int = 64, min_chunk_size: int = 50) -> BenchmarkComparisonResult: ...
    def format_markdown_table(self, comparison: BenchmarkComparisonResult) -> str: ...
```

```bash
# Run pytest verification suite and benchmark CLI
.venv/bin/pytest tests/unit/test_benchmark.py tests/unit/test_structure.py -v
PYTHONPATH=src .venv/bin/python -m ingestion.cli benchmark
# Result: 142 passed in 0.34s
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Benchmark Engine:** Implemented `src/ingestion/benchmark.py` with `StrategyBenchmarkRunner`, `BenchmarkStrategyMetrics`, and `BenchmarkComparisonResult`.
2. [x] **CLI Subcommand & Flag:** Integrated `benchmark` subcommand and `--benchmark` option in `src/ingestion/cli.py`.
3. [x] **Package Export:** Exported benchmark symbols in `src/ingestion/__init__.py`.
4. [x] **Unit Testing:** Implemented `tests/unit/test_benchmark.py` and updated `tests/unit/test_structure.py`.
5. [x] **Quality Assurance:** Verified 100% compliance with `mypy --explicit-package-bases src config tests`, `ruff check`, and full pytest suite (142 passed).
