# Implementation Roadmap: Automated Document Ingestion Pipeline & Information Loss Audit

> **Goal:** Step-by-step technical implementation guide from initial workspace setup to verified production CLI release.

---

## 📊 Phase Overview

```text
Phase 1: Baseline Setup ──► Phase 2: Domain Schemas ──► Phase 3: Loaders & Cleaner ──► Phase 4: Chunking Strategies
Phase 5: Loss Audit    ──► Phase 6: Orchestration   ──► Phase 7: CLI Interface     ──► Phase 8: Verification & Release
```

---

## Phase 1: Technical Baseline & Infrastructure Setup

### Entry Criteria & Dependencies
- Python `>= 3.11` installed.
- Access to project root directory `projects/6_RAG_pipeline`.

### Tasks
- [ ] **Step 1.1: Environment Initialization:** Configure `pyproject.toml` with Poetry dependencies (`pydantic>=2.0`, `tiktoken`, `typer`, `rich`, `pytest`, `mypy`, `ruff`).
- [ ] **Step 1.2: Tooling & Code Quality Setup:** Configure `ruff.toml` and `mypy` strict mode (`--strict`). Set up `Makefile` shortcuts (`install`, `lint`, `test`).
- [ ] **Step 1.3: Directory Structure Creation:** Scaffold package hierarchy under `src/ingestion/` (`__init__.py`, `models.py`, `exceptions.py`, `loaders.py`, `cleaner.py`, `chunkers.py`, `monitor.py`, `pipeline.py`, `cli.py`) and test directories `tests/unit/`, `tests/integration/`, `tests/fixtures/`.

### Verification Checkpoints
- Running `poetry run mypy src/` executes without configuration errors.
- Running `make lint` passes basic checks.

---

## Phase 2: Domain Schemas, Exceptions & Data Contracts

### Entry Criteria & Dependencies
- Phase 1 completed.

### Tasks
- [ ] **Step 2.1: Custom Exception Hierarchy:** Implement `src/ingestion/exceptions.py` with base `IngestionError` and derived errors (`DocumentLoadError`, `CleanError`, `ChunkError`, `AuditError`).
- [ ] **Step 2.2: Immutable Pydantic Domain Models:** Implement `src/ingestion/models.py` defining `BaseDomainModel` (`frozen=True`, `extra="forbid"`), `StrategyType`, `IngestionConfig`, `LoadedDocument`, `Chunk`, `DocumentReport`, and `IngestionReport`.

### Verification Checkpoints
- Unit tests verify domain models reject extra fields and prevent field mutations (`frozen=True`).

---

## Phase 3: Document Loaders & Text Cleaning Engine

### Entry Criteria & Dependencies
- Phase 2 completed.

### Tasks
- [ ] **Step 3.1: Document Loader Abstraction:** Implement `src/ingestion/loaders.py` with `DocumentLoader(ABC)` interface and `TextMarkdownLoader` concrete implementation. Calculate deterministic SHA-256 `document_id`.
- [ ] **Step 3.2: Text Cleaning Engine:** Implement `src/ingestion/cleaner.py` (`TextCleaner`) supporting NFKC normalization, whitespace capping ($\le 2$ consecutive `\n`), and repetitive header/footer line deduplication.
- [ ] **Step 3.3: Structural Protection Shielding:** Add regular expression shielding to `TextCleaner` to bypass Markdown tables (`^\|.*\|$`) and fenced code blocks (```) during stripping operations.

### Verification Checkpoints
- Unit tests in `tests/unit/test_loaders.py` and `tests/unit/test_cleaner.py` pass cleanly.
- Markdown table formatting is 100% preserved after text cleaning.

---

## Phase 4: Strategy-Pattern Chunking Engine & Tokenization

### Entry Criteria & Dependencies
- Phase 3 completed.

### Tasks
- [ ] **Step 4.1: Tokenizer & Strategy Interfaces:** Implement `src/ingestion/tokenizers.py` (`BaseTokenizer(ABC)` interface + `GeminiEncoder`, `TiktokenEncoder`, `HeuristicTokenizer`) and `src/ingestion/chunkers.py` (`ChunkingStrategy` ABC with dependency injection).
- [ ] **Step 4.2: Fixed-Size Token Chunker:** Implement `FixedSizeChunker` utilizing a sliding window algorithm based on exact token counts from the injected `BaseTokenizer` instance.
- [ ] **Step 4.3: Recursive Structural Chunker:** Implement `RecursiveStructuralChunker` with hierarchical delimiter splitting (`["\n# ", "\n## ", "\n### ", "\n\n", "\n", ". ", " "]`).

### Verification Checkpoints
- Unit tests in `tests/unit/test_tokenizers.py` and `tests/unit/test_chunkers.py` verify exact token limits per chunk across Gemini and OpenAI tokenizers.
- Recursive chunker preserves heading structures without exceeding max token bounds.


---

## Phase 5: Information Loss Audit & Quality Monitor

### Entry Criteria & Dependencies
- Phase 4 completed.

### Tasks
- [ ] **Step 5.1: Character Coverage & Overlap Auditing:** Implement `src/ingestion/monitor.py` (`IngestionMonitor`) to compute `char_coverage_ratio` ($\ge 0.98$) and `duplicate_char_ratio`.
- [ ] **Step 5.2: Orphan Block Detector:** Implement regex scanner to detect Markdown tables and code blocks split across chunk boundaries, populating `orphan_blocks` count.
- [ ] **Step 5.3: Token Delta & Metric Computation:** Calculate `token_count_delta` and `undersized_chunks_ratio`, generating complete `DocumentReport` and aggregated `IngestionReport`.

### Verification Checkpoints
- Unit tests in `tests/unit/test_monitor.py` detect deliberate table boundary splits and flag `orphan_blocks > 0`.

---

## Phase 6: Pipeline Orchestrator & Serialization

### Entry Criteria & Dependencies
- Phase 5 completed.

### Tasks
- [ ] **Step 6.1: Pipeline Orchestrator Facade:** Implement `src/ingestion/pipeline.py` (`PipelineOrchestrator`) coordinating Loaders ──► Cleaner ──► Chunkers ──► Monitor ──► Exporters.
- [ ] **Step 6.2: File-Level Exception Shielding:** Wrap per-file ingestion steps to record error tracebacks into `DocumentReport.errors` without crashing directory batch runs.
- [ ] **Step 6.3: JSONL & Audit Report Exporters:** Write JSONL chunk serializer (`data/output/chunks.jsonl`) and global JSON audit report exporter (`rapport_ingestion.json`).

### Verification Checkpoints
- Integration test in `tests/integration/test_pipeline.py` processes synthetic corpus fixtures and produces valid JSONL + JSON outputs.

---

## Phase 7: CLI Interface & Rich Console UI

### Entry Criteria & Dependencies
- Phase 6 completed.

### Tasks
- [ ] **Step 7.1: Typer CLI Commands:** Implement `src/ingestion/cli.py` creating the `ingest` command with CLI parameters (`--input`, `--output`, `--strategy`, `--chunk-size`, `--overlap`, `--min-chunk-size`, `--report`).
- [ ] **Step 7.2: Rich Terminal Output:** Implement Rich console status tables displaying per-file coverage, orphan blocks, token deltas, and overall execution status.
- [ ] **Step 7.3: Exit Code Gatekeeper:** Force non-zero exit code (`1`) when `has_blocking_alerts` is `True` to break failing CI builds.

### Verification Checkpoints
- Executing `poetry run ingest --input ./tests/fixtures/ --output ./data/output/` outputs Rich summary table.
- System exits with code `1` on corrupted fixtures or fixed chunking table splits, and code `0` on recursive chunking.

---

## Phase 8: Verification, Benchmarking & Release

### Entry Criteria & Dependencies
- Phase 7 completed.

### Tasks
- [ ] **Step 8.1: Synthetic Test Corpus:** Build test fixtures in `tests/fixtures/` (`01_clean_doc.md`, `02_noisy_header.txt`, `03_table_split.md`, `04_corrupted_encoding.txt`).
- [ ] **Step 8.2: Comparative Strategy Benchmark:** Run benchmark comparing `FixedSizeChunker` vs `RecursiveStructuralChunker` over synthetic corpus, documenting metrics in `README.md`.
- [ ] **Step 8.3: Quality Gates & Final Delivery:** Execute 100% `mypy --strict` typing check, full `pytest` suite coverage ($\ge 85\%$), and `ruff` linting.

### Verification Checkpoints
- `make lint` and `make test` pass without warnings or errors.
- Final deliverable `rapport_ingestion.json` generated and verified against system specifications.
