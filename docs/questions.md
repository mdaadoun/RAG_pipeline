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

