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
  - **`tests/unit/test_tooling.py`:** Unit tests validating ruff.toml, pyproject.toml MyPy strict configuration, and Makefile shortcuts.
  - **`tests/unit/test_structure.py`:** Unit tests validating package directory structure, test subdirectories, custom exception hierarchy, and exports.

---

## ⚙️ 2. Technical Function Breakdown & Flow

### Configuration & Environment Setup

#### `config/settings.py`
- **`Settings(BaseSettings)`:** Environment schema model defining log level, chunking parameters, input/output paths, and character coverage thresholds (`0.98`).
- **`get_settings() -> Settings`:** Thread-safe LRU-cached accessor returning the global application settings instance.

#### `config/logging.py`
- **`setup_logging(log_level: str = "INFO") -> None`:** Initializes `structlog` processors for ISO-8601 timestamps, log level tagging, context variable merging, and JSON rendering.
- **`get_logger(name: str = "ingestion") -> Any`:** Factory function returning a bound structured logger instance.

### Custom Exception Hierarchy & Structure

#### `src/ingestion/exceptions.py`
- **`IngestionError(Exception)`:** Base exception for all ingestion pipeline errors.
- **`DocumentLoadError(IngestionError)`:** Exception raised when loading or parsing a source document fails.
- **`CleanError(IngestionError)`:** Exception raised when text cleaning or normalization encounters an error.
- **`ChunkError(IngestionError)`:** Exception raised during document text chunking operations.
- **`AuditError(IngestionError)`:** Exception raised when quality audit checks or thresholds fail.

#### `src/ingestion/__init__.py`
- **Package Root:** Re-exports core domain models (`Document`, `Chunk`, `IngestionMetrics`, `AuditReport`) and custom exception classes (`IngestionError`, `DocumentLoadError`, `CleanError`, `ChunkError`, `AuditError`) in `__all__`.

### Quality Assurance & Tooling Tests

#### `tests/unit/test_structure.py`
- **`test_package_directory_structure_exists()`:** Verifies all required package files exist in `src/ingestion/`.
- **`test_test_directories_exist()`:** Verifies required test subdirectories (`unit/`, `integration/`, `fixtures/`) exist.
- **`test_custom_exception_hierarchy()`:** Validates custom exception class hierarchy and inheritance.
- **`test_package_exports()`:** Confirms package root exports all core models and exception symbols.

#### `tests/unit/test_tooling.py`
- **`test_ruff_config_exists_and_valid()`:** Validates existence and parsing of standalone `ruff.toml` linting rules.
- **`test_pyproject_mypy_strict_mode()`:** Confirms `pyproject.toml` enables MyPy strict mode and typed def enforcement.
- **`test_makefile_targets_defined()`:** Verifies `Makefile` contains standard target shortcuts (`install`, `lint`, `test`, `dev`, `clean`).

#### `tests/unit/test_env.py`
- **`test_environment_settings_defaults()`:** Validates default environment properties and threshold bounds.
- **`test_get_settings_caching()`:** Verifies identity (`is`) of cached settings instances across calls.
- **`test_logging_setup()`:** Ensures structlog logger configuration executes cleanly.
- **`test_core_dependencies_available()`:** Confirms `pydantic`, `structlog`, and `tiktoken` BPE encoders are importable and functional.

---

## 📦 3. Manifest & Automation

- **`ruff.toml`:** Dedicated Ruff static linter and formatter configuration (rules E, W, F, I, B, UP, SIM, RUF).
- **`pyproject.toml`:** Dependency declarations (Poetry), CLI scripts, MyPy strict options, Pytest coverage rules.
- **`Makefile`:** Shortcuts (`make install`, `make lint`, `make test`, `make dev`, `make clean`, `make docker-build`).
- **`Dockerfile`:** Multi-stage production container image specification.

