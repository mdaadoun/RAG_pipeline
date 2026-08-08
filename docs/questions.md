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
