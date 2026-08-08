# System Architecture Specification: Automated Document Ingestion Pipeline & Information Loss Audit

> **Status:** Active Standard | **Version:** 1.0.0 | **Scope:** `projects/6_RAG_pipeline`

---

## 1. System Topology & Layered Architecture Flow

The system strictly adheres to a top-down, decoupled layered architecture. Presentation, Orchestration, Core Domain, and Infrastructure/Adapters interact across explicit boundary interfaces.

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER (CLI & UI)                         │
│                  src/ingestion/cli.py (Typer, Rich Console UI)                  │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Input Arguments & Config
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER (Pipeline Facade)                    │
│                src/ingestion/pipeline.py (PipelineOrchestrator)                │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
       ┌─────────────────────────────────┼─────────────────────────────────┐
       ▼                                 ▼                                 ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│   STAGE 1: LOADERS      │   │   STAGE 2: CLEANER      │   │   STAGE 3: CHUNKERS     │
│   src/ingestion/        │   │   src/ingestion/        │   │   src/ingestion/        │
│   loaders.py            │   │   cleaner.py            │   │   chunkers.py           │
│   - DocumentLoader(ABC) │   │   - TextCleaner         │   │   - ChunkingStrategy    │
│   - TextMarkdownLoader  │   │   - NFKC Normalization  │   │     (ABC)               │
│                         │   │   - Boilerplate Dedupe  │   │   - FixedSizeChunker    │
│                         │   │   - Block Shielding     │   │   - RecursiveChunker    │
└────────────┬────────────┘   └────────────┬────────────┘   └────────────┬────────────┘
             │ LoadedDocument              │ Cleaned Text                │ List[Chunk]
             └─────────────────────────────┼─────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     STAGE 4: AUDIT & MONITORING ENGINE                          │
│                   src/ingestion/monitor.py (IngestionMonitor)                   │
│   - Character Coverage Ratio (≥ 0.98)      - Duplicate Character Ratio          │
│   - Table/Code Orphan Detection            - Token Count Delta Offset           │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ DocumentReport / IngestionReport
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      STAGE 5: INFRASTRUCTURE & SERIALIZATION                    │
│                      - JSONL Exporter (data/output/*.jsonl)                     │
│                      - Audit Report Exporter (rapport_ingestion.json)           │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       CORE DATA CONTRACTS & SCHEMAS                             │
│                  src/ingestion/models.py & exceptions.py                        │
│            (Pydantic V2 Immutable Models: frozen=True, extra="forbid")          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. AI Architecture Enforcement Rules

> ⚠️ **STRICT COMPLIANCE:** Any diff violating these rules MUST be rejected.

### Rule 1: Layered Dependency Flow
- Flow is strictly top-down: `CLI / Entry` ──> `Pipeline Orchestrator` ──> `Core Stages (Loaders, Cleaner, Chunkers, Monitor)` ──> `Data Contracts & Exceptions`.
- Leaf modules (`models.py`, `exceptions.py`) MUST NOT import higher-level pipeline or orchestrator modules.

### Rule 2: Exception Shielding ("Zero Naked Crash")
- Raw I/O exceptions (`UnicodeDecodeError`, `FileNotFoundError`, `OSError`) must never bubble up unhandled to crash the pipeline process.
- All domain-specific errors inherit from a single root class: `IngestionError`.
- For multi-file batch execution, file-level errors MUST be captured inside `DocumentReport.errors` without halting execution of remaining files.

### Rule 3: Deterministic Data Contracts & State
- All layer boundaries exchange immutable Pydantic V2 models (`model_config = ConfigDict(frozen=True, extra="forbid")`).
- Tokenization via `tiktoken` (`cl100k_base` / `gpt-4o` standard) MUST be 100% deterministic given identical inputs and configurations.

### Rule 4: Audit Observability & Metrics Enforcement
- The pipeline MUST evaluate every processed document for structural and content fidelity:
  1. `char_coverage_ratio`: Unique character preservation ($\ge 0.98$).
  2. `duplicate_char_ratio`: Overlap deviation monitoring.
  3. `orphan_blocks`: Mid-table or mid-code boundary breaks (MUST be `0`).
  4. `token_count_delta`: Total token offset tracking between cleaned source and output chunks.

### Rule 5: Pure Logic & Side-Effect Isolation
- Chunking strategies (`ChunkingStrategy`), cleaning logic (`TextCleaner`), and monitoring algorithms (`IngestionMonitor`) MUST operate as pure functions without file system side effects.
- File system reads, directory scans, and JSON/JSONL writes are strictly isolated in `loaders.py`, `cli.py`, or explicit I/O adapters.

### Rule 6: Guardrails & Structural Protection
- Cleaning procedures MUST NOT perform line stripping or whitespace normalization on protected blocks (Markdown tables starting with `|` and code blocks fenced by `````).

---

## 3. Core Contract Specification

```python
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class BaseDomainModel(BaseModel):
    """Immutable base model for all ingestion contracts."""
    model_config = ConfigDict(frozen=True, extra="forbid")

class StrategyType(str, Enum):
    FIXED = "fixed"
    RECURSIVE = "recursive"

class IngestionConfig(BaseDomainModel):
    input_path: Path
    output_path: Path
    strategy: StrategyType = StrategyType.RECURSIVE
    chunk_size: int = Field(default=512, gt=0)
    overlap: int = Field(default=64, ge=0)
    min_chunk_size: int = Field(default=50, ge=0)
    boilerplate_threshold: int = Field(default=3, ge=1)
    report_path: Path = Path("rapport_ingestion.json")

class LoadedDocument(BaseDomainModel):
    document_id: str = Field(description="SHA-256 hash derived from source path and length")
    source_path: Path = Field(description="File path to source document")
    raw_content: str = Field(description="Unprocessed text string read from disk")
    file_size_bytes: int = Field(ge=0, description="Source file size in bytes")

class Chunk(BaseDomainModel):
    id: str = Field(description="Unique deterministic chunk ID: {document_id}_{chunk_index}")
    document_id: str = Field(description="Parent document identifier")
    content: str = Field(description="Extracted chunk text payload")
    start_char: int = Field(ge=0, description="Start character offset in cleaned source")
    end_char: int = Field(ge=0, description="End character offset in cleaned source")
    token_count: int = Field(ge=0, description="Exact token count computed via Tiktoken")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Contextual metadata tags")

class DocumentReport(BaseDomainModel):
    document_id: str
    source_path: str
    char_coverage_ratio: float = Field(ge=0.0, le=1.0)
    duplicate_char_ratio: float = Field(ge=0.0)
    orphan_blocks: int = Field(ge=0, description="Count of broken markdown tables or code blocks")
    token_count_delta: int = Field(description="Difference between source tokens and net chunk tokens")
    undersized_chunks_ratio: float = Field(ge=0.0, le=1.0)
    chunk_count: int = Field(ge=0)
    status: str = Field(description="'ok' | 'warning' | 'error'")
    errors: List[str] = Field(default_factory=list)

class IngestionReport(BaseDomainModel):
    corpus_path: str
    strategy_used: StrategyType
    execution_timestamp: datetime = Field(default_factory=datetime.utcnow)
    documents: List[DocumentReport]
    total_chunks: int = Field(ge=0)
    global_char_coverage_ratio: float = Field(ge=0.0, le=1.0)
    documents_in_error: int = Field(ge=0)
    has_blocking_alerts: bool = Field(description="True if any file raised errors or orphan_blocks > 0")
```

---

## 4. Component Interfaces & Component Architecture

### 4.1 Loader Abstraction (`DocumentLoader`)
- **Abstract Class:** `DocumentLoader(ABC)` exposing `@abstractmethod load(path: Path) -> LoadedDocument`.
- **Implementation:** `TextMarkdownLoader` supports `.txt` and `.md` ingestion, calculates deterministic `document_id` using SHA-256 hash.

### 4.2 Text Cleaning Engine (`TextCleaner`)
- **Pipeline:**
  1. `unicodedata.normalize("NFKC", text)` for character standardisation.
  2. Whitespace capped to maximum `2` consecutive `\n` characters.
  3. Repetitive header/footer line removal if occurrence count $> N$ (`boilerplate_threshold`).
  4. Structural block protection: Lines matching `^\|.*\|$` (tables) and ``` block boundaries are bypassed during line stripping.

### 4.3 Strategy Pattern Chunking Engine & Model-Agnostic Tokenization (`ChunkingStrategy` & `BaseTokenizer`)
- **Tokenizer Abstraction:** `BaseTokenizer(ABC)` exposing `@abstractmethod encode`, `decode`, and `count_tokens`. Implementations include `GeminiEncoder` (Gemini model API / calibrated fallback), `TiktokenEncoder` (OpenAI BPE), and `HeuristicTokenizer`.
- **Abstract Base Strategy:** `ChunkingStrategy(ABC)` with `@abstractmethod chunk(doc_or_text, doc_id) -> list[Chunk]`, injecting a `BaseTokenizer` instance.
- **`FixedSizeChunker`:** Token sliding-window algorithm based on exact token `chunk_size` and `overlap` calculated by the injected `BaseTokenizer`.
- **`RecursiveStructuralChunker`:** Hierarchical splitter evaluating split delimiters in order:
  `["\n# ", "\n## ", "\n### ", "\n\n", "\n", ". ", " "]`.

### 4.4 Information Loss Auditor (`IngestionMonitor`)
- **Character Coverage Set:** Computes char index bitset over cleaned text vs. character ranges in generated `Chunk`s.
- **Orphan Block Detection:** Uses regex patterns for Markdown tables (`(\n\|[^\n]+\|\n)+`) and code blocks. Verifies if any chunk boundary cuts inside an active block range.

---

## 5. Resilience, Fault Isolation & Quality Controls

- **Batch Execution Safety:** Directory iteration wraps file loading in `try...except IngestionError`. Unreadable or corrupted files append an error entry to `DocumentReport` without halting the pipeline.
- **CI/CD Quality Control Rules:**
  - **Exit Code 0:** Execution succeeds, `has_blocking_alerts == False`.
  - **Exit Code 1:** Execution triggered blocking alerts (`documents_in_error > 0` or `orphan_blocks > 0`).

---

## 6. Tech Stack & Infrastructure Matrix

| Component | Tool / Standard | Requirement / Purpose |
| --- | --- | --- |
| **Language** | Python `>= 3.11` | Strict typing enforced via `mypy --strict` |
| **Data Contracts** | Pydantic V2 | Immutable models (`frozen=True`, `extra="forbid"`) |
| **CLI & Formatting** | Typer & Rich | Terminal user interface & structured tables |
| **Tokenization** | Model-Agnostic (`GeminiEncoder` / `TiktokenEncoder`) | Google Gemini (`gemini-1.5-flash`) & OpenAI (`cl100k_base`) |
| **Linting & Code Style**| Ruff & Pytest | Quality verification and continuous integration |


---

## 7. Trade-Off Analysis & Risk Mitigations

| Risk / Architectural Trade-off | Description | Mitigation Strategy |
| --- | --- | --- |
| **Fixed vs. Recursive Chunking Trade-off** | Fixed chunking is computationally faster but creates orphan table cells. | Enforce `RecursiveStructuralChunker` as primary production default. |
| **Memory Overhead on Large Files** | Loading multi-gigabyte files into memory causes process OOM. | Impose loading size caps & stream buffers in `DocumentLoader`. |
| **Boilerplate Over-Cleaning** | Aggressive line deduplication may strip legitimate repeated Markdown syntax. | Mask structured blocks (tables & code blocks) before deduplication pass. |