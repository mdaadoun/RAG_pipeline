# Session 3.1: Document Loader Abstraction & SHA-256 ID Generation
**Date:** 2026-08-08

Designed and implemented a modular document loader abstraction in `src/ingestion/loaders.py`, rooted at `DocumentLoader(ABC)` with concrete implementations `TextLoader`, `MarkdownLoader`, and `TextMarkdownLoader`. Replaced random UUID identifiers with deterministic SHA-256 document IDs (`doc_<hash>`), introduced a factory accessor `get_loader()`, trapped low-level I/O and encoding exceptions into domain `DocumentLoadError` objects, and expanded unit tests in `tests/unit/test_loaders.py`.

---

### 1. 🎓 Concepts Introduced
- **Document Loader Interface (`DocumentLoader`):** Abstract contract decoupling raw file format reading logic from downstream pipeline cleaning, chunking, and auditing.
- **Deterministic SHA-256 Document Identifiers (`doc_<hash>`):** Generating reproducible document keys from file names and contents to ensure idempotent pipeline runs and consistent audit metrics across executions.
- **File System & Encoding Exception Shielding:** Trapping low-level OS (`OSError`, `FileNotFoundError`) and decoding (`UnicodeDecodeError`) errors inside loader helper methods and wrapping them into structured `DocumentLoadError` domain exceptions.
- **Loader Factory Routing (`get_loader`):** Encapsulating extension-to-loader mapping logic so caller code dynamically obtains the appropriate format loader without hardcoding extension checks.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Abstract Base Class Interface (DocumentLoader)]
- **Option 1:** Passing raw file paths directly to pipeline steps without an abstraction layer.
- **Option 2 (Selected):** Defined `DocumentLoader(ABC)` with flexible path resolution supporting both `DocumentLoader(path).load()` and `loader.load(path)` invocation styles.

#### [ADR-02: Deterministic SHA-256 ID Calculation]
- **Option 1:** Using `uuid.uuid4()` for document IDs.
- **Option 2 (Selected):** Implemented `compute_document_id(file_name, content)` producing `doc_{sha256(filename:content)[:12]}`. Ensures identical input documents generate identical document IDs across runs.

#### [ADR-03: Centralized Exception Shielding]
- **Option 1:** Allowing raw `FileNotFoundError` or `UnicodeDecodeError` to escape to top-level callers.
- **Option 2 (Selected):** Trapped I/O and decoding errors in `_resolve_path()` and `_read_content()`, re-raising `DocumentLoadError` equipped with file metadata context.

#### [ADR-04: Extensible Factory Pattern (get_loader)]
- **Option 1:** Hardcoding format conditionals in `IngestionPipeline`.
- **Option 2 (Selected):** Created `get_loader(file_path)` factory mapping file extensions (`.md`, `.txt`) to concrete loaders or raising `DocumentLoadError` for unsupported extensions.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/loaders.py
from abc import ABC, abstractmethod
import hashlib
from pathlib import Path

from ingestion.exceptions import DocumentLoadError
from ingestion.models import LoadedDocument

def compute_document_id(file_name: str, content: str) -> str:
    """Compute deterministic SHA-256 document identifier."""
    digest = hashlib.sha256(f"{file_name}:{content}".encode()).hexdigest()[:12]
    return f"doc_{digest}"

class DocumentLoader(ABC):
    """Abstract base class for document loaders."""

    def __init__(self, file_path: str | Path | None = None) -> None:
        self.file_path = Path(file_path) if file_path else None

    @abstractmethod
    def load(self, file_path: str | Path | None = None) -> LoadedDocument:
        """Load target source file and return typed domain model."""
        pass

class TextLoader(DocumentLoader): ...
class MarkdownLoader(DocumentLoader): ...
class TextMarkdownLoader(DocumentLoader): ...

def get_loader(file_path: str | Path) -> DocumentLoader:
    """Factory returning appropriate loader for given file extension."""
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext in (".md", ".markdown"):
        return MarkdownLoader(path)
    if ext in (".txt", ".text"):
        return TextLoader(path)
    raise DocumentLoadError(f"Unsupported file format: '{ext}'", details={"file_path": str(path)})
```

```bash
# Validation commands executed
.venv/bin/pytest tests/unit/test_loaders.py
.venv/bin/mypy src/
.venv/bin/ruff check src/ tests/
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Document Loader Abstraction:** Created `DocumentLoader(ABC)`, `TextLoader`, `MarkdownLoader`, and `TextMarkdownLoader` in `src/ingestion/loaders.py`.
2. [x] **Deterministic Identifiers:** Implemented `compute_document_id()` utilizing SHA-256 digests.
3. [x] **Factory Function:** Added `get_loader()` for format routing and exception shielding for unsupported file extensions.
4. [x] **Package Exports & Pipeline Integration:** Exported loader classes in `src/ingestion/__init__.py` and updated `IngestionPipeline` in `src/ingestion/pipeline.py`.
5. [x] **Unit Testing Suite:** Expanded `tests/unit/test_loaders.py` and `tests/unit/test_structure.py`, verifying 39 passing tests and 100% type/lint compliance.
