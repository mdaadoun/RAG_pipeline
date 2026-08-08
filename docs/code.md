# Codebase Structure & Technical Function Reference

> **Overview:** Comprehensive reference guide for directory layout, module contracts, function breakdowns, and technical design flow.

---

## 🛠️ 1. Directory Structure

- **`config/`:** Centralized environment configuration and structured logging setup.
  - **`config/settings.py`:** Type-safe settings model backed by `pydantic-settings` with LRU caching.
  - **`config/logging.py`:** Structured JSON logging configurator using `structlog`.
- **`src/ingestion/`:** Modular RAG document ingestion pipeline components.
  - **`cli.py`:** Typer CLI entrypoint with Rich UI console tables and exit code gatekeeper.
  - **`pipeline.py`:** Orchestrator facade driving loaders ──► cleaner ──► chunkers ──► monitor ──► exporters.
  - **`models.py`:** Immutable domain models (`IngestionConfig`, `LoadedDocument`, `Chunk`, `AuditReport`).
  - **`exceptions.py`:** Hierarchy inheriting from base `IngestionError`.
  - **`loaders.py`:** Abstract loader interface and concrete text/markdown file loaders.
  - **`cleaner.py`:** Text cleaner engine supporting NFKC normalization and protected Markdown shielding.
  - **`chunkers.py`:** Fixed-size token chunker and recursive structural heading chunker via `tiktoken`.
  - **`monitor.py`:** Quality assurance and information loss audit engine computing coverage & orphan block metrics.
- **`tests/`:** Unit and integration test suite.
  - **`tests/unit/test_env.py`:** Unit tests verifying environment settings, logging, and core package imports.

---

## ⚙️ 2. Technical Function Breakdown & Flow

### Configuration & Environment Setup

#### `config/settings.py`
- **`Settings(BaseSettings)`:** Environment schema model defining log level, chunking parameters, input/output paths, and character coverage thresholds (`0.98`).
- **`get_settings() -> Settings`:** Thread-safe LRU-cached accessor returning the global application settings instance.

#### `config/logging.py`
- **`setup_logging(log_level: str = "INFO") -> None`:** Initializes `structlog` processors for ISO-8601 timestamps, log level tagging, context variable merging, and JSON rendering.
- **`get_logger(name: str = "ingestion") -> Any`:** Factory function returning a bound structured logger instance.

### System Verification & Tests

#### `tests/unit/test_env.py`
- **`test_environment_settings_defaults()`:** Validates default environment properties and threshold bounds.
- **`test_get_settings_caching()`:** Verifies identity (`is`) of cached settings instances across calls.
- **`test_logging_setup()`:** Ensures structlog logger configuration executes cleanly.
- **`test_core_dependencies_available()`:** Confirms `pydantic`, `structlog`, and `tiktoken` BPE encoders are importable and functional.

---

## 📦 3. Manifest & Automation

- **`pyproject.toml`:** Dependency declarations (Poetry), CLI scripts, tool rules (`ruff`, `mypy`, `pytest`).
- **`Makefile`:** Shortcuts (`make install`, `make lint`, `make test`, `make dev`, `make clean`).
- **`Dockerfile`:** Container image specification.
