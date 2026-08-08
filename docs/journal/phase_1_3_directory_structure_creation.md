# Session 1.3: Directory Structure Creation & Custom Exception Hierarchy
**Date:** 2026-08-08

Scaffolded modular package hierarchy under `src/ingestion/`, established dedicated test subdirectories (`tests/unit/`, `tests/integration/`, `tests/fixtures/`), implemented custom domain exception hierarchy in `src/ingestion/exceptions.py`, and verified package structure via unit tests.

---

### 1. 🎓 Concepts Introduced
- **Package Hierarchy:** Structured python package layout separating data contracts, loaders, transformations, chunkers, quality audit monitors, and CLI presentation.
- **Custom Exception Hierarchy:** Object-oriented error classification allowing granular error catching (e.g. `DocumentLoadError`, `ChunkError`) while maintaining a single root exception (`IngestionError`).
- **Test Runner Registration:** Structuring tests into standard Pytest module hierarchies (`tests/unit/`, `tests/integration/`) for automated discovery and execution in test runners.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Modular Package Scaffolding]
- **Option 1:** Monolithic script or flat file layout for all ingestion components.
- **Option 2 (Selected):** Scaffolded `src/ingestion/` package hierarchy with single-responsibility modules (`__init__.py`, `models.py`, `exceptions.py`, `loaders.py`, `cleaner.py`, `chunkers.py`, `monitor.py`, `pipeline.py`, `cli.py`). Enforces strict layer isolation and maintainability (<250 LOC per module).

#### [ADR-02: Custom Domain Exception Hierarchy]
- **Option 1:** Throwing generic `RuntimeError` or built-in Python exceptions.
- **Option 2 (Selected):** Implemented `src/ingestion/exceptions.py` defining base `IngestionError` and derived exception classes (`DocumentLoadError`, `CleanError`, `ChunkError`, `AuditError`). Enables fine-grained error handling and clean traceback reporting without swallowing unrelated runtime exceptions.

#### [ADR-03: Test Suite Hierarchy]
- **Option 1:** Mixing unit tests, integration tests, and test fixtures in a single flat directory.
- **Option 2 (Selected):** Structured tests into `unit/`, `integration/`, and `fixtures/` subdirectories with `test_structure.py` for package verification. Separates fast isolated unit tests from integration workloads and synthetic data files.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/exceptions.py
class IngestionError(Exception):
    """Base exception for all ingestion pipeline errors."""
    pass

class DocumentLoadError(IngestionError):
    """Exception raised when loading or parsing a source document fails."""
    pass

class CleanError(IngestionError):
    """Exception raised when text cleaning or normalization encounters an error."""
    pass

class ChunkError(IngestionError):
    """Exception raised during document text chunking operations."""
    pass

class AuditError(IngestionError):
    """Exception raised when quality audit checks or thresholds fail."""
    pass
```

```bash
# Validation commands executed
PYTHONPATH=src pytest
mypy src config tests
ruff check src config tests
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Package Hierarchy:** Scaffolded `src/ingestion/` package modules (`__init__.py`, `models.py`, `exceptions.py`, `loaders.py`, `cleaner.py`, `chunkers.py`, `monitor.py`, `pipeline.py`, `cli.py`).
2. [x] **Custom Exception Hierarchy:** Implemented `src/ingestion/exceptions.py` with base `IngestionError` and derived stage-specific exceptions.
3. [x] **Test Directory Hierarchy:** Established `tests/unit/`, `tests/integration/`, and `tests/fixtures/`.
4. [x] **Unit Testing & Verification:** Created `tests/unit/test_structure.py` verifying package file existence, test subdirectories, exception inheritance, and package exports.
