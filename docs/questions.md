# Technical Interview & Architecture FAQ

> **Overview:** Interview Q&As and technical rationale covering environment setup, configuration management, logging telemetry, and static analysis.

---

### Q1: Why use `pydantic-settings` over standard `os.environ` or manual dictionary loading?
**Answer:** `pydantic-settings` automatically handles env variable parsing, type coercion, default values, and schema validation. It converts unvalidated string environment inputs into typed, immutable configuration objects with early runtime error detection and fail-fast startup behavior.

---

### Q2: What advantages does `structlog` provide over standard Python logging for RAG pipelines?
**Answer:** `structlog` produces machine-readable JSON log events with context variable merging (e.g. `document_id`, `chunk_index`, `token_count`). This enables observability platforms to index metrics and trace document flow across pipeline stages without brittle regex log parsing.

---

### Q3: Why enforce `mypy --strict` during initial environment setup rather than post-development?
**Answer:** Enforcing `mypy --strict` from Step 1 prevents architectural debt, ensures explicit domain data signatures, and guarantees zero untyped boundaries across loaders, cleaner, chunkers, and audit monitor components.

---

### Q4: Why enforce MyPy strict mode in a Python RAG pipeline instead of relying on standard dynamic typing?
**Answer:** RAG pipelines process unstructured text data and pass complex data objects (Documents, Chunks, AuditReports) between loaders, cleaners, chunkers, and monitors. Enforcing MyPy strict mode guarantees interface contracts, prevents NullPointer/AttributeError crashes during batch runs, and documents function signatures explicitly.

---

### Q5: What is the advantage of using Ruff over traditional Python linters like Flake8, Black, and Isort?
**Answer:** Ruff is written in Rust and executes 10-100x faster than traditional Python tools. It unifies linting, import sorting, and code formatting into a single tool with zero-dependency execution, significantly reducing CI run times.

---

### Q6: How does Makefile standardization improve code quality across team environments?
**Answer:** Makefile provides standardized command shortcuts (`make lint`, `make test`) that abstract underlying tooling details. This ensures developer environments match CI/CD runner environments exactly, preventing 'works on my machine' issues.

---

### Q7: Why create a dedicated `exceptions.py` module with a custom exception hierarchy instead of using built-in Python exceptions?
**Answer:** A custom hierarchy rooted at `IngestionError` enables callers and orchestrators to catch subsystem-specific failures (`DocumentLoadError`, `CleanError`, `ChunkError`) without catching unrelated system exceptions. It standardizes error handling across pipeline stages and simplifies logging and audit reporting.

---

### Q8: How does separating `tests/unit/`, `tests/integration/`, and `tests/fixtures/` impact build pipelines and maintainability?
**Answer:** It allows fast, isolated execution of lightweight unit tests during local development while isolating complex multi-component pipeline runs and synthetic test files, facilitating targeted test discovery and clear test reporting.

---

### Q9: Why export core exceptions and models directly from `ingestion.__init__`?
**Answer:** It provides a clean public API contract for external consumers and CLI commands, avoiding deep internal module imports and reducing coupling to internal package layout.

---

### Q10: Why create a custom exception hierarchy rooted at `IngestionError` instead of using standard Python built-in exceptions?
**Answer:** Custom exception hierarchies isolate domain-specific errors from standard runtime errors. It allows pipeline orchestrators to catch any ingestion failure via `except IngestionError:` without catching unrelated system bugs like `KeyError` or `AttributeError`, while enabling stage-specific audit tracking.

---

### Q11: What benefit does the `details` dictionary payload and `to_dict()` method provide to the ingestion pipeline?
**Answer:** The `details` dictionary captures contextual metadata (such as document IDs, invalid characters, or file paths) at the error site. The `to_dict()` method provides a clean dictionary representation for JSON serialization into `DocumentReport` objects and external observability tools.

---

### Q12: How does the exception hierarchy support non-crashing directory batch ingestion?
**Answer:** The batch pipeline orchestrator wraps per-file ingestion stages in `try...except IngestionError as exc:`. Caught exceptions are serialized using `exc.to_dict()` and attached to the file's `DocumentReport.errors` list, allowing batch execution to continue uninterrupted for remaining files.

---

### Q13: Why use Pydantic `ConfigDict(frozen=True, extra="forbid")` for RAG domain models?
**Answer:** Immutability (`frozen=True`) prevents accidental data mutation during text processing pipeline stages, ensuring audit reproducibility. Forbidding extra fields (`extra="forbid"`) catches schema drift, typo bugs, and unexpected API inputs early at the domain boundary.

---

### Q14: How does inheriting from `BaseDomainModel` enforce strict typing and domain integrity?
**Answer:** `BaseDomainModel` centralizes schema configuration, guaranteeing all downstream models (`LoadedDocument`, `Chunk`, `DocumentReport`, `IngestionReport`) inherit identical immutability and strict validation rules without duplicating configuration code across modules.

---

### Q15: How are backward compatibility and domain evolvability achieved when refactoring models?
**Answer:** By creating alias mappings (e.g. `Document = LoadedDocument`) and property getters (e.g. `Chunk.document_id` pointing to `doc_id`), new strict schemas can be introduced without breaking pre-existing code that relies on legacy attribute names.
