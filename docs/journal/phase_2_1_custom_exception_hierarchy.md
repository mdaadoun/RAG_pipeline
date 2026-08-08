# Session 2.1: Custom Exception Hierarchy
**Date:** 2026-08-08

Designed and implemented a production-ready custom exception hierarchy rooted at `IngestionError` in `src/ingestion/exceptions.py`, enriched base exceptions with structured `details` dictionary payloads and `to_dict()` serialization, created dedicated unit tests in `tests/unit/test_exceptions.py`, and verified clean test execution and MyPy type safety.

---

### 1. 🎓 Concepts Introduced
- **Unified Domain Exception Root:** Establishing `IngestionError` as the base class for all pipeline exceptions to enable polymorphic exception handling (`except IngestionError:`).
- **Structured Error Serialization:** Equipping exception instances with a `to_dict()` method to allow seamless JSON serialization for audit reporting and logging.
- **Contextual Exception Payloads:** Supporting an optional `details: dict[str, Any]` parameter on exception initializers to capture key-value error metadata at failure sites.
- **Polymorphic Error Handling:** Software design pattern where callers catch multiple distinct stage error types using their common base class (`IngestionError`).

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Rooted Custom Exception Hierarchy]
- **Option 1:** Throwing generic Python built-in exceptions (`RuntimeError`, `ValueError`, `IOError`).
- **Option 2 (Selected):** Implemented a unified custom exception hierarchy rooted at `IngestionError`. Enables orchestrators to catch pipeline-specific failures cleanly without swallowing unrelated system or standard runtime errors.

#### [ADR-02: Enriched Contextual Exception Payloads]
- **Option 1:** Standard Python `Exception` subclasses with message-only strings.
- **Option 2 (Selected):** Extended `IngestionError` initializer with `message: str` and `details: dict[str, Any] | None = None`, accompanied by `to_dict()`. Facilitates structured JSON reporting in `DocumentReport.errors` without requiring external logging dependencies.

#### [ADR-03: Stage-Specific Exception Subclasses]
- **Option 1:** Using `IngestionError` for all pipeline failures.
- **Option 2 (Selected):** Derived 4 distinct stage exceptions (`DocumentLoadError`, `CleanError`, `ChunkError`, `AuditError`). Allows fine-grained recovery, targeted retry strategies per phase, and precise telemetry tagging.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/exceptions.py
from typing import Any

class IngestionError(Exception):
    """Base exception for all document ingestion pipeline errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception context to dictionary representation."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }

class DocumentLoadError(IngestionError):
    """Raised when loading or parsing a source document fails."""
    pass

class CleanError(IngestionError):
    """Raised when text cleaning or normalization encounters an error."""
    pass

class ChunkError(IngestionError):
    """Raised during document text chunking operations."""
    pass

class AuditError(IngestionError):
    """Raised when quality audit checks or thresholds fail."""
    pass
```

```bash
# Validation commands executed
.venv/bin/pytest tests/unit/test_exceptions.py
.venv/bin/mypy src/ tests/
.venv/bin/ruff check src/ tests/
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Custom Exception Implementation:** Enhanced `src/ingestion/exceptions.py` with typed `IngestionError` base class and derived exceptions (`DocumentLoadError`, `CleanError`, `ChunkError`, `AuditError`).
2. [x] **Structured Serialization:** Added `to_dict()` method and `details` payload dictionary support.
3. [x] **Unit Testing Suite:** Created `tests/unit/test_exceptions.py` covering inheritance, polymorphic catching, details payload, and `to_dict()` formatting.
4. [x] **Verification:** Verified 100% test pass rate across 25 unit/integration tests and MyPy strict compliance.
