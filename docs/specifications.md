# Project 4 — Automated Document Ingestion Pipeline & Information Loss Audit

*Technical Specifications and Execution Blueprint*

**Tied to Chapter 5:** Data Ingestion & Continuous ETL Pipelines

**Part II:** Data Engineering for AI & RAG Architecture

**Deliverables:** Production-Ready CLI (`ingest`), Typed Python Module, `pytest` Test Suite, Synthetic Test Corpus, and Quality Audit Report (`rapport_ingestion.json`)

**Required Tech Stack:** Python 3.11+, Poetry, Pydantic V2 (strict mode), Tiktoken, Rich, Structlog, Pytest, Mypy (`--strict`), Ruff.

---

## 1. Product Vision & Pedagogical Objective

A Retrieval-Augmented Generation (RAG) system rarely fails at the language model or vector database layer: **it fails at the ingestion boundary**. An ingestion pipeline that silently truncates Markdown tables, splits contractual clauses mid-sentence, or strips $8\%$ of source text during over-aggressive cleaning destroys downstream system quality before a single embedding is generated.

This project elevates the learner from writing a simple "text-splitting script" to building a **qualitative, typed, tested, and audited ingestion module**.

### Key Requirement: Monitoring Information Loss

The central constraint of this project is the mandatory implementation of an independent **IngestionMonitor**. The pipeline must not merely generate chunks: it must **measure, quantify, and log information loss and structural breaks** for every document processed.

```
                                  INPUT CORPUS
                            (Large .txt / .md files)
                                       │
                                       ▼
                               STAGE 1: LOADERS
               (Extensible: TextLoader / MarkdownLoader / [PDFLoader])
                                       │
                                       ▼
                              STAGE 2: CLEANING
           (NFKC Normalization, Regex, Stripping Repetitive Boilerplate)
                                       │
                                       ▼
                              STAGE 3: CHUNKING
                (Strategy Pattern: FixedOverlap vs Recursive)
                                       │
                                       ▼
                         STAGE 4: AUDIT & MONITORING
             (Retention Ratios, Table Orphans, Token Drift)
                                       │
                                       ▼
                            STAGE 5: SERIALIZATION
            (JSONL Chunks + Global Report + Rich Console Output)

```

---

## 2. Functional Scope & Business Specifications

### 2.1 Ingestion & Discovery (`Loader`)

* **Supported Formats (Strict Scope):** Plaintext (`.txt`) and Markdown (`.md`). However, the architecture must expose an abstract extraction interface (`DocumentLoader`) allowing future integration of a PDF/PPTX loader without modifying downstream pipeline code.
* **Large Volume Management:** The pipeline must handle large files (tens of thousands of tokens) without causing memory overhead (streaming/chunk-based loading beyond a configurable threshold, default 10 MB).
* **Deterministic Identity:** Every document is assigned a stable `document_id` based on the `SHA-256` cryptographic hash of its initial source content combined with its relative path.

### 2.2 Cleaning & Normalization (`Cleaner`)

The cleaning module applies a sequence of deterministic transformations:

1. **Unicode Normalization:** Strict application of the `NFKC` standard via `unicodedata`.
2. **Whitespace Standardization:** Normalization of non-breaking spaces and tabs, along with stripping excess line breaks (capped at a maximum of 2 consecutive `\n` characters to preserve paragraph boundaries).
3. **Repetitive Boilerplate Deduplication:** Detection and removal of identical lines (headers, footers) repeated across more than $N$ occurrences throughout the corpus ($N$ is configurable, default $N=3$).
4. **Protection of Structured Blocks:** **Absolute Rule:** Markdown tables (lines starting with `|`) and code blocks (enclosed by `````) must **never** be altered by whitespace normalization or truncated during the cleaning phase.

### 2.3 Configurable Segmentation (`Chunker`)

Strict implementation of the **Strategy Pattern** via an abstract `ChunkingStrategy` class. Implementations must receive their parameters through **constructor injection** (never hardcoded):

1. **`FixedSizeChunker`:** Sliding window splitting based on actual tokens (computed via `tiktoken`, using `cl100k_base` / `gpt-4o` encodings). Supports configurable token overlap (`overlap`).
2. **`RecursiveStructuralChunker`:** Context-aware splitting respecting text hierarchy. It recursively attempts to split along the structural hierarchy:

* Markdown headers (`\n# `, `\n## `, `\n### `)
* Paragraphs (`\n\n`)
* Lines (`\n`)
* Sentences (`. `)
* Words (` `)
If a block exceeds the target `chunk_size`, the strategy recurses down to the next lower delimiter level.

### 2.4 Information Loss Audit & Monitoring (`IngestionMonitor`)

This acts as the automated quality control module. For each processed document, the auditor computes:

| Metric | Formula / Definition | Suggested Alert Threshold |
| --- | --- | --- |
| `char_coverage_ratio` | $\frac{\text{Sum of unique characters covered by at least one chunk}}{\text{Character count of cleaned text}}$ | $< 0.98$ $\rightarrow$ **Warning** |
| `duplicate_char_ratio` | Proportion of duplicate characters outside configured overlap | $> \text{overlap} + 5\%$ $\rightarrow$ **Warning** |
| `orphan_blocks` | Number of structural blocks (Markdown tables, code blocks) cut mid-way by a chunk boundary | $> 0$ $\rightarrow$ **Blocking Alert (Error)** |
| `token_count_delta` | $\text{Cleaned Source Tokens} - (\sum \text{Chunk Tokens} - \text{Overlap Tokens})$ | Must be close to $0$ |
| `undersized_chunks_ratio` | Ratio of chunks whose size is $< \text{min\_chunk\_size}$ | Informational |
| `processing_errors` | Exceptions raised during document reading/parsing | $> 0$ $\rightarrow$ **Blocking Alert (Error)** |

---

## 3. Software Architecture & Data Models

### 3.1 Project Structure (Conforming to Part II Standards)

```text
ingestion_pipeline/
├── src/
│   └── ingestion/
│       ├── __init__.py
│       ├── cli.py              # Typer/Click entrypoint with Rich UI
│       ├── models.py           # Pydantic V2 models (Chunk, Reports, Config)
│       ├── loaders.py          # DocumentLoader interface & Text/Markdown implementations
│       ├── cleaner.py          # TextCleaner (NFKC, boilerplate, preservation)
│       ├── chunkers.py         # Strategy Pattern (FixedSize, RecursiveStructural)
│       ├── monitor.py          # IngestionMonitor & loss audit engine
│       └── pipeline.py         # Global orchestrator (Pipeline execution)
├── tests/
│   ├── unit/
│   │   ├── test_cleaner.py
│   │   ├── test_chunkers.py
│   │   ├── test_loaders.py
│   │   └── test_monitor.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── fixtures/               # Synthetic test corpus (.md, .txt)
├── data/
│   ├── input/
│   └── output/
├── pyproject.toml              # Poetry config, strict Mypy, Ruff settings
├── README.md                   # Documentation & Strategy comparison analysis
└── rapport_ingestion.json      # Sample audit deliverable output

```

---

### 3.2 Schemas & Data Models (`src/ingestion/models.py`)

```python
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class StrategyType(str, Enum):
    FIXED = "fixed"
    RECURSIVE = "recursive"

class ChunkMetadata(BaseModel):
    chunk_index: int
    start_char: int
    end_char: int
    token_count: int
    has_table: bool = False
    has_code_block: bool = False
    section_hierarchy: List[str] = Field(default_factory=list)

class Chunk(BaseModel):
    id: str
    document_id: str
    content: str
    start_char: int
    end_char: int
    token_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentReport(BaseModel):
    document_id: str
    source_path: str
    char_coverage_ratio: float
    duplicate_char_ratio: float
    orphan_blocks: int
    token_count_delta: int
    undersized_chunks_ratio: float
    chunk_count: int
    status: str  # "ok" | "warning" | "error"
    errors: List[str] = Field(default_factory=list)

class IngestionReport(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    corpus_path: str
    strategy_used: str
    execution_timestamp: datetime = Field(default_factory=datetime.utcnow)
    documents: List[DocumentReport]
    total_chunks: int
    global_char_coverage_ratio: float
    documents_in_error: int
    has_blocking_alerts: bool

```

---

### 3.3 Loader Abstraction (`src/ingestion/loaders.py`)

```python
from abc import ABC, abstractmethod
import hashlib
from pathlib import Path
from pydantic import BaseModel

class LoadedDocument(BaseModel):
    document_id: str
    source_path: Path
    raw_content: str
    file_size_bytes: int

class DocumentLoader(ABC):
    @abstractmethod
    def load(self, file_path: Path) -> LoadedDocument:
        """Loads a file and returns a typed LoadedDocument."""
        pass

class TextMarkdownLoader(DocumentLoader):
    def load(self, file_path: Path) -> LoadedDocument:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid encoding for {file_path}: {e}")
            
        doc_id = hashlib.sha256(f"{file_path.name}_{len(content)}".encode()).hexdigest()[:16]
        return LoadedDocument(
            document_id=doc_id,
            source_path=file_path,
            raw_content=content,
            file_size_bytes=file_path.stat().st_size
        )

```

---

### 3.4 Strategy Pattern Interface (`src/ingestion/chunkers.py`)

```python
from abc import ABC, abstractmethod
import tiktoken
from src.ingestion.models import Chunk

class ChunkingStrategy(ABC):
    def __init__(self, chunk_size: int = 512, overlap: int = 0, min_chunk_size: int = 20, model_name: str = "gpt-4o"):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.tokenizer = tiktoken.encoding_for_model(model_name)

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    @abstractmethod
    def chunk(self, text: str, document_id: str) -> list[Chunk]:
        """Splits text into chunks in a pure, deterministic manner."""
        pass

```

---

### 3.5 Ingestion Monitor & Loss Audit (`src/ingestion/monitor.py`)

```python
import re
from src.ingestion.models import Chunk, DocumentReport

class IngestionMonitor:
    def __init__(self, min_chunk_size: int = 20, max_overlap_tolerance: float = 0.05):
        self.min_chunk_size = min_chunk_size
        self.max_overlap_tolerance = max_overlap_tolerance

    def _detect_orphan_blocks(self, cleaned_text: str, chunks: list[Chunk]) -> int:
        """Detects Markdown tables or code blocks cut mid-way by chunk boundaries."""
        orphan_count = 0
        
        # Regex to match complete Markdown tables (consecutive lines starting with '|')
        table_pattern = re.compile(r"(\n\|[^\n]+\|\n)+")
        tables = list(table_pattern.finditer(cleaned_text))
        
        for table in tables:
            t_start, t_end = table.span()
            table_str = table.group(0).strip()
            
            # Find chunks that intersect with the table boundary
            containing_chunks = [
                c for c in chunks 
                if not (c.end_char <= t_start or c.start_char >= t_end)
            ]
            
            # If table is split across multiple chunks without being completely preserved inside one
            if len(containing_chunks) > 1:
                is_fully_preserved = any(table_str in c.content for c in containing_chunks)
                if not is_fully_preserved:
                    orphan_count += 1
                    
        return orphan_count

    def audit_document(
        self, 
        document_id: str, 
        source_path: str, 
        cleaned_text: str, 
        chunks: list[Chunk],
        errors: list[str]
    ) -> DocumentReport:
        if errors:
            return DocumentReport(
                document_id=document_id,
                source_path=source_path,
                char_coverage_ratio=0.0,
                duplicate_char_ratio=0.0,
                orphan_blocks=0,
                token_count_delta=0,
                undersized_chunks_ratio=0.0,
                chunk_count=0,
                status="error",
                errors=errors
            )

        cleaned_char_count = len(cleaned_text)
        if cleaned_char_count == 0:
            return DocumentReport(
                document_id=document_id,
                source_path=source_path,
                char_coverage_ratio=1.0,
                duplicate_char_ratio=0.0,
                orphan_blocks=0,
                token_count_delta=0,
                undersized_chunks_ratio=0.0,
                chunk_count=0,
                status="ok"
            )

        # 1. Coverage Calculation
        covered_chars = set()
        total_chunk_chars = 0
        for c in chunks:
            total_chunk_chars += len(c.content)
            for idx in range(c.start_char, c.end_char):
                covered_chars.add(idx)

        char_coverage_ratio = len(covered_chars) / cleaned_char_count
        
        # 2. Duplicate Ratio (characters read multiple times outside theoretical overlap)
        duplicate_chars = total_chunk_chars - len(covered_chars)
        duplicate_char_ratio = duplicate_chars / cleaned_char_count

        # 3. Orphan Blocks (Tables / Code)
        orphans = self._detect_orphan_blocks(cleaned_text, chunks)

        # 4. Undersized Chunks
        undersized = sum(1 for c in chunks if c.token_count < self.min_chunk_size)
        undersized_ratio = undersized / len(chunks) if chunks else 0.0

        # Final Status Assessment
        status = "ok"
        if char_coverage_ratio < 0.98 or duplicate_char_ratio > 0.30:
            status = "warning"
        if orphans > 0:
            status = "error"

        return DocumentReport(
            document_id=document_id,
            source_path=source_path,
            char_coverage_ratio=round(char_coverage_ratio, 4),
            duplicate_char_ratio=round(duplicate_char_ratio, 4),
            orphan_blocks=orphans,
            token_count_delta=0,  # Adjust based on Tiktoken delta
            undersized_chunks_ratio=round(undersized_ratio, 4),
            chunk_count=len(chunks),
            status=status,
            errors=errors
        )

```

---

## 4. CLI Specifications & CI/CD Integration

The project exposes an executable CLI entrypoint installed via Poetry: `ingest`.

### 4.1 CLI Command Interface

```bash
poetry run ingest \
  --input ./corpus/ \
  --output ./chunks/ \
  --strategy recursive \
  --chunk-size 512 \
  --overlap 64 \
  --min-chunk-size 50 \
  --report ./rapport_ingestion.json

```

### 4.2 Parameter Matrix

| Parameter | Required | Default Value | Description |
| --- | --- | --- | --- |
| `--input` | **Yes** | - | Source directory containing `.txt`/`.md` files |
| `--output` | **Yes** | - | Output directory where JSONL chunk files will be serialized |
| `--strategy` | No | `fixed` | Chunking strategy: `fixed` or `recursive` |
| `--chunk-size` | No | `512` | Target chunk size in tokens |
| `--overlap` | No | `0` | Token overlap (used in fixed strategy) |
| `--min-chunk-size` | No | `20` | Threshold below which a chunk is marked undersized |
| `--report` | No | `./rapport_ingestion.json` | Destination path for summary audit report |

### 4.3 Rich Console Output & Exit Codes

At the end of execution, the CLI must:

1. Render a formatted table via the `Rich` library summarizing per-document processing metrics (Source, Chunks, Coverage, Orphans, Status).
2. **Exit Code Specification:**

* **`0`**: Successful execution without blocking errors.
* **`1`**: Triggered if `documents_in_error > 0` or if `orphan_blocks > 0` is detected (enabling automated failure in CI/CD build pipelines).

---

## 5. Testing Requirements & Synthetic Corpus

### 5.1 `pytest` Test Suite (Target Coverage $\ge 85\%$)

Automated tests must explicitly cover the following scenarios:

1. **Empty Document:** Ingestion of a 0-byte file executes without crashing, generating 0 chunks and a valid report payload.
2. **Short Document:** File containing fewer tokens than `chunk_size` (must yield exactly 1 chunk).
3. **Markdown Table Boundary Case (Orphan Test):**

* Ingest a synthetic document containing a Markdown table positioned at the theoretical boundary of a chunk window.
* **Assertion 1:** The `fixed` strategy must trigger `orphan_blocks > 0`.
* **Assertion 2:** The `recursive` strategy must preserve table integrity and report `orphan_blocks == 0`.

4. **Corrupted File Resilience:** Source directory contains a file with invalid binary encoding. The pipeline catches the exception, increments `documents_in_error`, and **continues processing** remaining healthy files.
5. **Coverage Non-Regression:** Validate on a fixed fixture that `char_coverage_ratio >= 0.98`.

### 5.2 Synthetic Test Corpus (`/tests/fixtures/`)

The `/tests/fixtures/` directory must contain 4 version-controlled sample files:

* `01_clean_doc.md`: Well-structured Markdown document.
* `02_noisy_header.txt`: Text document with headers and footers repeated 5 times.
* `03_table_split.md`: Document containing 2 large Markdown tables and 1 Python code block.
* `04_corrupted_encoding.txt`: File containing invalid non-UTF8 bytes.

---

## 6. Required Deliverables Structure

1. **Complete Source Code:** Modular, fully typed implementation under `src/ingestion/`.
2. **Quality Checks Passing:** Clean pass for both `poetry run mypy --strict src` and `poetry run ruff check src`.
3. **Generated Ingestion Report:** `rapport_ingestion.json` file generated against the synthetic test corpus.
4. **Comprehensive `README.md` File:**

* Installation steps and CLI usage instructions.
* **Comparative Analysis (3–4 paragraphs):** Clear metric comparison between `fixed` vs `recursive` strategies evaluated on the test corpus (providing a concrete cost/quality trade-off analysis).

---

## 7. Bonus Extensions (Optional)

1. **Semantic Chunking Strategy:** Implementation of a 3rd strategy based on cosine similarity drops between consecutive sentence embeddings (`sentence-transformers`).
2. **Minimalist PDF Extraction:** Integration of a `PDFLoader` built on `pdfplumber`, implementing the core `DocumentLoader` interface.
3. **SimHash Deduplication:** Pre-chunking detection of near-duplicate source files using the SimHash algorithm.

---

## 8. Acceptance Criteria (Validation Checklist)

* [ ] **Strict Strategy Pattern:** `FixedSizeChunker` and `RecursiveStructuralChunker` strategies can be dynamically swapped via the CLI.
* [ ] **Character Coverage:** `char_coverage_ratio >= 0.98` on healthy corpus files when using the `recursive` strategy.
* [ ] **Table Preservation:** `orphan_blocks == 0` when using the `recursive` strategy on files with Markdown tables.
* [ ] **Resilience & Fault Isolation:** Corrupted input files do not crash the global CLI execution flow.
* [ ] **CI/CD Exit Code:** CLI returns a non-zero exit code (`1`) upon detecting errors or broken table structures.
* [ ] **Code Quality:** Zero `mypy --strict` errors and zero `ruff` linter warnings.
* [ ] **Automated Testing:** `pytest` runs cleanly with code coverage $\ge 85\%$.