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
  - **`models.py`:** Immutable Pydantic domain models (`BaseDomainModel`, `StrategyType`, `IngestionConfig`, `LoadedDocument`, `Chunk`, `DocumentReport`, `IngestionReport`, `IngestionMetrics`, `AuditReport`).
  - **`exceptions.py`:** Hierarchy inheriting from base `IngestionError`.
  - **`loaders.py`:** Abstract loader interface and concrete text/markdown file loaders.
  - **`cleaner.py`:** Text cleaner engine supporting NFKC normalization, whitespace capping, boilerplate deduplication, and protected Markdown shielding.
  - **`chunkers.py`:** Fixed-size token chunker and recursive structural heading chunker via `tiktoken`.
  - **`monitor.py`:** Quality assurance and information loss audit engine computing coverage & orphan block metrics.
- **`tests/`:** Unit and integration test suite.
  - **`tests/unit/test_cleaner.py`:** Unit tests verifying NFKC normalization, whitespace capping, line deduplication, structural shielding, and CleanError handling.
  - **`tests/unit/test_models.py`:** Unit tests verifying domain model immutability (`frozen=True`), extra field rejection (`extra="forbid"`), StrategyType enum, and aliases.
  - **`tests/unit/test_env.py`:** Unit tests verifying environment settings, logging, and core package imports.
  - **`tests/unit/test_exceptions.py`:** Unit tests verifying exception hierarchy inheritance, details payloads, to_dict serialization, and polymorphic error handling.
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

### Domain Schemas & Data Contracts

#### `src/ingestion/models.py`
- **`BaseDomainModel(BaseModel)`:** Base immutable Pydantic V2 domain model configured with `frozen=True` and `extra="forbid"`.
- **`StrategyType(str, Enum)`:** String-backed enumeration defining `FIXED` ("fixed") and `RECURSIVE` ("recursive") chunking strategies.
- **`IngestionConfig(BaseDomainModel)`:** Validates execution parameters for chunking size, overlap, minimum size, coverage threshold (`0.98`), and directory paths.
- **`LoadedDocument(BaseDomainModel)`:** Domain model for loaded source documents with `char_count` and `token_count` property accessors. Aliased to `Document`.
- **`Chunk(BaseDomainModel)`:** Model for document text slices containing character boundaries, token counts, orphan block flags, and `document_id` property alias.
- **`DocumentReport(BaseDomainModel)`:** Per-document structural audit report encapsulating coverage ratios, duplicate ratios, and orphan block counts.
- **`IngestionReport(BaseDomainModel)`:** Global structured audit deliverable tracking total chunks, global character coverage, document errors, and execution timestamp.
- **`IngestionMetrics(BaseDomainModel)` & `AuditReport(BaseDomainModel)`:** Legacy aggregate statistical metrics models maintained for backward compatibility.

#### `src/ingestion/__init__.py`
- **Package Root:** Re-exports core domain models (`BaseDomainModel`, `StrategyType`, `IngestionConfig`, `LoadedDocument`, `Document`, `Chunk`, `DocumentReport`, `IngestionMetrics`, `IngestionReport`, `AuditReport`), custom exceptions (`IngestionError`, `DocumentLoadError`, `CleanError`, `ChunkError`, `AuditError`), and document loaders (`DocumentLoader`, `TextLoader`, `MarkdownLoader`, `TextMarkdownLoader`, `get_loader`, `compute_document_id`) in `__all__`.

### Custom Exception Hierarchy & Structure

#### `src/ingestion/exceptions.py`
- **`IngestionError(message: str, details: dict[str, Any] | None = None)`:** Base domain exception for all ingestion pipeline errors equipped with structured `details` metadata and `to_dict()` serialization.
- **`IngestionError.to_dict() -> dict[str, Any]`:** Serializes exception class name, message string, and contextual details payload into a JSON-compatible dictionary.
- **`DocumentLoadError(IngestionError)`:** Exception raised when loading or parsing a source document fails.
- **`CleanError(IngestionError)`:** Exception raised when text cleaning or normalization encounters an error.
- **`ChunkError(IngestionError)`:** Exception raised during document text chunking operations.
- **`AuditError(IngestionError)`:** Exception raised when quality audit checks or thresholds fail.

### Document Loaders & Format Ingestion

#### `src/ingestion/loaders.py`
- **`compute_document_id(file_name: str, content: str) -> str`:** Computes a deterministic SHA-256 hex digest (`doc_<hash>`) derived from UTF-8 string `f"{file_name}:{content}"`.
- **`DocumentLoader(ABC)`:** Abstract base class for file loaders providing path resolution (`_resolve_path`) and content reading (`_read_content`) with `DocumentLoadError` exception shielding.
- **`TextLoader(DocumentLoader)`:** Concrete loader parsing `.txt` plain text files into `LoadedDocument` domain objects.
- **`MarkdownLoader(DocumentLoader)`:** Concrete loader parsing `.md`/`.markdown` files into `LoadedDocument` domain objects.
- **`TextMarkdownLoader(DocumentLoader)`:** Generic document loader supporting auto-detection of text vs markdown formats.
- **`get_loader(file_path: str | Path) -> DocumentLoader`:** Factory function returning the concrete loader instance based on file extension, or raising `DocumentLoadError` for unsupported file extensions.

### Text Cleaning & Structural Protection Shielding

#### `src/ingestion/cleaner.py`
- **`TextCleaner(__init__)`:** Configures options for Unicode normalization, control character removal, newline capping bounds (`max_newlines`), boilerplate line threshold, and structural protection shielding.
- **`TextCleaner.clean(text: str, boilerplate_threshold: int | None = None) -> str`:** Coordinates the cleaning pipeline: shields protected blocks, normalizes Unicode (NFKC), strips control bytes, standardizes spaces, deduplicates boilerplate lines, caps newlines, and restores protected blocks wrapped in `CleanError`.
- **`TextCleaner.extract_protected_blocks(text: str) -> list[tuple[int, int, str]]`:** Scans document text with regular expressions to locate span boundaries of fenced code blocks (``` / ~~~) and Markdown tables (|...|).
- **`TextCleaner._shield_protected_blocks(text: str) -> tuple[str, dict[str, str]]`:** Replaces protected spans with unique UUID-tagged placeholder tokens (`___SHIELDED_<uuid>_<idx>___`) and returns text along with the placeholder lookup dict.
- **`TextCleaner._unshield_protected_blocks(text: str, placeholders: dict[str, str]) -> str`:** Restores original shielded block strings into their respective placeholder locations.
- **`TextCleaner._deduplicate_boilerplate(text: str, threshold: int) -> str`:** Computes line frequencies across unshielded text lines and removes non-empty lines exceeding the configured occurrence threshold.

### Text Cleaner Unit Tests

#### `tests/unit/test_cleaner.py`
- **`test_cleaner_nfkc_normalization()`:** Verifies NFKC character normalization, non-breaking space replacement, and control character removal.
- **`test_extract_protected_blocks()`:** Validates boundary extraction for fenced code blocks and Markdown tables.
- **`test_whitespace_standardization_and_capping()`:** Confirms excess newlines ($\ge 3$) are capped to `max_newlines` (default 2) and line trailing whitespace is trimmed.
- **`test_boilerplate_line_deduplication()`:** Tests frequency-based line pruning for lines repeating more than `boilerplate_threshold` times.
- **`test_structural_protection_shielding()`:** Verifies code blocks and Markdown tables preserve exact formatting, indentation, and newlines during cleaning.
- **`test_cleaner_error_handling()`:** Ensures `CleanError` is raised on invalid non-string input types.
- **`test_cleaner_configurable_options()`:** Validates behavior when unicode normalization, newline capping, or boilerplate deduplication are disabled.


### Document Loader Unit Tests

#### `tests/unit/test_loaders.py`
- **`test_document_loader_abc_instantiation()`:** Verifies `DocumentLoader` ABC cannot be directly instantiated.
- **`test_markdown_loader()`:** Validates `MarkdownLoader` content extraction and metadata properties.
- **`test_text_loader()`:** Validates `TextLoader` content extraction and metadata properties.
- **`test_text_markdown_loader_auto_detect()`:** Tests dynamic format auto-detection for text and markdown documents.
- **`test_deterministic_document_id()`:** Verifies deterministic SHA-256 document ID generation.
- **`test_loader_file_not_found()`:** Verifies `DocumentLoadError` is raised when target file path does not exist.
- **`test_loader_invalid_encoding()`:** Verifies `DocumentLoadError` is raised when reading non-UTF-8 binary data.
- **`test_get_loader_factory()`:** Tests factory routing by file extension and error handling for unsupported formats.

### Domain Model Unit Tests

#### `tests/unit/test_models.py`
- **`test_base_domain_model_immutability_and_extra_forbid()`:** Verifies `BaseDomainModel` enforces `frozen=True` and `extra="forbid"` on child classes.
- **`test_strategy_type_enum()`:** Validates string representation and value parsing for `StrategyType.FIXED` and `StrategyType.RECURSIVE`.
- **`test_ingestion_config_defaults_and_validation()`:** Verifies `IngestionConfig` default parameters and validation bounds.
- **`test_loaded_document_and_alias()`:** Tests `LoadedDocument` instantiation, `Document` alias identity, and `char_count`/`token_count` properties.
- **`test_chunk_model_properties_and_immutability()`:** Confirms `Chunk` field requirements, `document_id` property accessor, and field mutation rejection.
- **`test_document_report_model()`:** Validates per-document report defaults, status fields, and immutability.
- **`test_ingestion_report_model()`:** Ensures `IngestionReport` timestamp auto-generation, list nesting, and immutability.
- **`test_audit_report_and_metrics_immutability()`:** Verifies immutability of legacy `IngestionMetrics` and `AuditReport` models.

### Quality Assurance & Tooling Tests

#### `tests/unit/test_structure.py`
- **`test_package_directory_structure_exists()`:** Verifies all required package files exist in `src/ingestion/`.
- **`test_test_directories_exist()`:** Verifies required test subdirectories (`unit/`, `integration/`, `fixtures/`) exist.
- **`test_custom_exception_hierarchy()`:** Validates custom exception class hierarchy and inheritance.
- **`test_package_exports()`:** Confirms package root exports all core model and exception symbols.

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
