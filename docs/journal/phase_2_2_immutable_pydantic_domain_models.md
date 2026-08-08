# Session 2.2: Immutable Pydantic Domain Models
**Date:** 2026-08-08

Designed and implemented production-ready immutable Pydantic V2 domain models in `src/ingestion/models.py`, rooted at `BaseDomainModel` configured with `frozen=True` and `extra="forbid"`. Implemented `StrategyType`, `IngestionConfig`, `LoadedDocument`, `Chunk`, `DocumentReport`, and `IngestionReport`, alongside backward-compatibility aliases and getters. Added comprehensive unit tests in `tests/unit/test_models.py` verifying model immutability, extra-field rejection, property logic, and static type safety.

---

### 1. 🎓 Concepts Introduced
- **Immutable Domain State (`frozen=True`):** Guaranteeing that domain objects (`LoadedDocument`, `Chunk`, `IngestionReport`) cannot be mutated post-creation, ensuring data audit reproducibility across pipeline steps.
- **Closed Schema Guarding (`extra="forbid"`):** Rejecting unexpected attributes during model instantiation to catch schema drift, typos, and bad API payloads at runtime boundaries.
- **Type-Safe Strategy Selection (`StrategyType`):** Utilizing string-backed Python enums to enforce valid chunking strategy parameters across CLI and orchestrator layers.
- **Backwards-Compatible Schema Evolution:** Exposing alias pointers (`Document = LoadedDocument`) and property wrappers (`Chunk.document_id`) to allow progressive domain model migration without breaking pre-existing code.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Centralized Immutable Base Model]
- **Option 1:** Define `model_config = ConfigDict(frozen=True, extra="forbid")` independently on every Pydantic model class.
- **Option 2 (Selected):** Created `BaseDomainModel(BaseModel)` as the common parent class for all ingestion schemas. Centralizes schema behavior rules and prevents configuration omission in future models.

#### [ADR-02: String-Backed Enum for Chunking Strategy]
- **Option 1:** Passing raw strings (`"fixed"`, `"recursive"`) in configuration dictionaries and parameters.
- **Option 2 (Selected):** Implemented `StrategyType(str, Enum)`. Combines string serializability with type-safe static checking by MyPy and IDE auto-completion.

#### [ADR-03: Zero-Breakage Compatibility Aliasing]
- **Option 1:** Rename existing models (`Document`) immediately across all existing pipeline modules, requiring risky refactoring.
- **Option 2 (Selected):** Defined `LoadedDocument` as the explicit domain model and exported `Document = LoadedDocument`, while adding property getter `document_id` on `Chunk`. Enables zero-downtime schema evolution.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/models.py
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class BaseDomainModel(BaseModel):
    """Base immutable Pydantic domain model forbidding extra fields."""
    model_config = ConfigDict(frozen=True, extra="forbid")

class StrategyType(str, Enum):
    """Supported document chunking strategies."""
    FIXED = "fixed"
    RECURSIVE = "recursive"

class IngestionConfig(BaseDomainModel):
    """Configuration model for document ingestion & chunking parameters."""
    strategy: StrategyType = Field(default=StrategyType.RECURSIVE)
    chunk_size: int = Field(default=512, gt=0)
    overlap: int = Field(default=64, ge=0)
    min_chunk_size: int = Field(default=50, ge=0)
    coverage_threshold: float = Field(default=0.98, ge=0.0, le=1.0)
    input_dir: str = Field(default="data/input")
    output_dir: str = Field(default="data/output")
    report_path: str = Field(default="rapport_ingestion.json")

class LoadedDocument(BaseDomainModel):
    """Domain model representing a loaded raw source document."""
    id: str = Field(...)
    file_path: str = Field(...)
    content: str = Field(...)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def char_count(self) -> int:
        return len(self.content)

    @property
    def token_count(self) -> int:
        return len(self.content.split())

Document = LoadedDocument

class Chunk(BaseDomainModel):
    """Domain model representing a sliced document text chunk."""
    id: str = Field(...)
    doc_id: str = Field(...)
    chunk_index: int = Field(default=0)
    content: str = Field(...)
    start_char: int = Field(...)
    end_char: int = Field(...)
    token_count: int = Field(...)
    is_orphan_block: bool = Field(default=False)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def document_id(self) -> str:
        return self.doc_id

class DocumentReport(BaseDomainModel):
    """Per-document structural audit report model."""
    document_id: str = Field(...)
    source_path: str = Field(...)
    char_coverage_ratio: float = Field(default=1.0)
    duplicate_char_ratio: float = Field(default=0.0)
    orphan_blocks: int = Field(default=0)
    token_count_delta: int = Field(default=0)
    undersized_chunks_ratio: float = Field(default=0.0)
    chunk_count: int = Field(default=0)
    status: str = Field(default="ok")
    errors: list[str] = Field(default_factory=list)

class IngestionReport(BaseDomainModel):
    """Global structured ingestion report deliverable."""
    corpus_path: str = Field(...)
    strategy_used: str = Field(...)
    execution_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    documents: list[DocumentReport] = Field(default_factory=list)
    total_chunks: int = Field(default=0)
    global_char_coverage_ratio: float = Field(default=1.0)
    documents_in_error: int = Field(default=0)
    has_blocking_alerts: bool = Field(default=False)
```

```bash
# Validation commands executed
.venv/bin/pytest tests/unit/test_models.py
.venv/bin/mypy src/
.venv/bin/ruff check src/ tests/
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Immutable Domain Schemas:** Implemented `BaseDomainModel`, `StrategyType`, `IngestionConfig`, `LoadedDocument`, `Chunk`, `DocumentReport`, and `IngestionReport` in `src/ingestion/models.py`.
2. [x] **Package Exports:** Updated `src/ingestion/__init__.py` to export all new domain model types.
3. [x] **Unit Testing Suite:** Created `tests/unit/test_models.py` covering model immutability, extra attribute rejection, validation rules, and property methods.
4. [x] **Verification:** Confirmed all 33 unit tests pass cleanly, MyPy strict type checking completes with 0 errors, and Ruff lints pass.
