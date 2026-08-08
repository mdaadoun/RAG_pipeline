# Session 5.3: Token Delta & Metric Computation
**Date:** 2026-08-08

Implemented `_compute_token_delta`, undersized chunks ratio calculation, and aggregate `IngestionReport` creation in `IngestionMonitor` to perform accurate token balance auditing and quality monitoring across document ingestion runs.

---

### 1. 🎓 Concepts Introduced
- **Token Count Delta (`token_count_delta`):** The numerical difference between cleaned source text tokens and net non-overlapping chunk tokens: $\text{Tokens}_\text{src} - (\sum \text{Tokens}_\text{chunks} - \sum \text{Tokens}_\text{overlap})$.
- **Undersized Chunks Ratio (`undersized_chunks_ratio`):** The proportion of generated document chunks whose token count is lower than `min_chunk_size`.
- **Overlap Compensation:** Token accounting technique that subtracts token counts of overlapping character regions between consecutive chunks to prevent false expansion metrics during audit.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Decoupled Token Encoder Injection]
- **Option 1:** Hardcoding a specific tokenizer inside `IngestionMonitor`.
- **Option 2 (Selected):** Injecting `BaseTokenizer` interface (`GeminiEncoder`, `TiktokenEncoder`, `HeuristicTokenizer`) into `IngestionMonitor`, allowing dynamic model-agnostic token counting.

#### [ADR-02: Overlap Compensation Formula]
- **Option 1:** Comparing raw sum of chunk tokens against source tokens without overlap adjustment.
- **Option 2 (Selected):** Re-tokenizing overlap spans between consecutive chunks and subtracting overlap token count from cumulative chunk tokens to achieve exact $\Delta_\text{token} = 0$ for non-lossy chunking.

#### [ADR-03: Informational Undersized Chunk Metric]
- **Option 1:** Triggering error status on undersized chunks.
- **Option 2 (Selected):** Categorizing undersized chunk ratio as an informational metric to prevent false-positive pipeline breaks on short section tails or header chunks.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/monitor.py
class IngestionMonitor:
    def __init__(
        self,
        min_chunk_size: int = 20,
        max_overlap_tolerance: float = 0.05,
        coverage_threshold: float = 0.98,
        tokenizer: BaseTokenizer | str | None = None,
    ) -> None:
        ...

    def _compute_token_delta(
        self,
        cleaned_text: str,
        chunks: list[Chunk],
        source_tokens: int | None = None,
    ) -> int:
        # Calculates net non-overlapping chunk tokens and computes source token delta
        ...

    def audit_document(...) -> DocumentReport:
        # Calculates character coverage, duplicates, orphan blocks, token delta, undersized ratio
        ...

    def create_ingestion_report(...) -> IngestionReport:
        # Constructs aggregated IngestionReport model with global metrics and blocking alert flags
        ...
```

```bash
# Verification suite execution
.venv/bin/pytest
PYTHONPATH=src .venv/bin/mypy --explicit-package-bases src tests config
.venv/bin/ruff check src tests config
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Token Delta Engine:** Implemented `_compute_token_delta` with overlap token subtraction logic.
2. [x] **Undersized Ratio Metric:** Added `undersized_chunks_ratio` calculation against `min_chunk_size`.
3. [x] **Aggregated IngestionReport:** Implemented `create_ingestion_report` to generate global deliverable reports.
4. [x] **Unit Testing & Verification:** Added unit tests in `tests/unit/test_monitor.py` covering exact token delta, undersized ratios, and blocking alert flags. All 76 pytest tests pass with 100% Mypy strict typing and Ruff linting compliance.
