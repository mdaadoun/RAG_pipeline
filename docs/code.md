# Codebase Structure & Technical Function Reference

> **Overview:** Comprehensive reference guide for directory layout, module contracts, function breakdowns, and technical design flow.

---

## 🛠️ 1. Directory Structure

- **`config/`:** Centralized environment configuration and structured logging setup.
  - **`config/settings.py`:** Type-safe settings model backed by `pydantic-settings` with LRU caching.
  - **`config/logging.py`:** Structured JSON logging configurator using `structlog`.
- **`src/ingestion/`:** Modular RAG document ingestion pipeline components.
  - **`cli.py`:** Typer CLI entrypoint with Rich UI console tables and exit code gatekeeper.
  - **`corpus.py`:** Synthetic test corpus manager (`SyntheticCorpus`, `SyntheticFixtureSpec`, `DEFAULT_FIXTURES`) handling benchmark fixture loading, self-healing creation, and integrity validation.
  - **`pipeline.py`:** Orchestrator facade driving loaders ──► cleaner ──► chunkers ──► monitor ──► exporters with per-stage exception shielding.
  - **`file_shield.py`:** File-level exception shielding primitives (`IngestionStage`, `StageError`, `FileShieldContext`) for per-stage traceback capture.
  - **`models.py`:** Immutable Pydantic domain models (`BaseDomainModel`, `StrategyType`, `IngestionConfig`, `LoadedDocument`, `Chunk`, `DocumentReport`, `IngestionReport`, `IngestionMetrics`, `AuditReport`).
  - **`exceptions.py`:** Hierarchy inheriting from base `IngestionError`.
  - **`loaders.py`:** Abstract loader interface and concrete text/markdown file loaders.
  - **`cleaner.py`:** Text cleaner engine supporting NFKC normalization, whitespace capping, boilerplate deduplication, and protected Markdown shielding.
  - **`chunkers.py`:** Fixed-size token chunker and recursive structural heading chunker via `tiktoken`.
  - **`exporters.py`:** Serialization exporters (`BaseExporter`, `JSONLChunkExporter`, `AuditReportExporter`) and procedural functions for JSONL chunks and JSON reports.
  - **`monitor.py`:** Quality assurance and information loss audit engine computing coverage & orphan block metrics.
- **`tests/`:** Unit and integration test suite.
  - **`tests/unit/test_exporters.py`:** Unit tests verifying JSONL stream/batch export, AuditReport and IngestionReport JSON formatting, deserialization, and error handling.
  - **`tests/unit/test_cleaner.py`:** Unit tests verifying NFKC normalization, whitespace capping, line deduplication, structural shielding, and CleanError handling.
  - **`tests/unit/test_models.py`:** Unit tests verifying domain model immutability (`frozen=True`), extra field rejection (`extra="forbid"`), StrategyType enum, and aliases.
  - **`tests/unit/test_monitor.py`:** Unit tests verifying character coverage ratio calculation, low coverage warning status, orphan Markdown table detection, empty document handling, duplicate character ratios, and report aggregation.
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
- **`test_table_pipe_shielding()`:** Verifies lines matching `^\|.*\|$` are shielded from whitespace capping and boilerplate line deduplication.
- **`test_tilde_code_block_shielding()`:** Verifies `~~~` fenced code blocks are extracted and shielded correctly.


### Model-Agnostic Tokenization Engine

#### `src/ingestion/tokenizers.py`
- **`BaseTokenizer(ABC)`:** Abstract base class defining model-agnostic token encoding contracts (`encode`, `decode`, `count_tokens`).
- **`TiktokenEncoder(BaseTokenizer)`:** Wrapper around OpenAI `tiktoken` BPE encodings (`cl100k_base` default or model names).
- **`GeminiEncoder(BaseTokenizer)`:** Tokenizer adapter for Google Gemini model API (`gemini-1.5-flash`) with calibrated SentencePiece offline fallback.
- **`HeuristicTokenizer(BaseTokenizer)`:** Lightweight character/word ratio token estimator for fast local execution.
- **`get_tokenizer(name_or_provider: str = "gemini") -> BaseTokenizer`:** Factory function routing to concrete tokenizer implementations by provider name.

### Strategy Pattern Chunking Engine

#### `src/ingestion/chunkers.py`
- **`ChunkingStrategy(ABC)`:** Abstract Base Class defining chunking strategy interface with parameter validation checks (`chunk_size > 0`, `overlap >= 0`, `overlap < chunk_size`, `min_chunk_size >= 0`) and injected `BaseTokenizer` instance.
- **`ChunkingStrategy.count_tokens / encode / decode`:** Delegation accessors forwarding token operations to the injected `BaseTokenizer`.
- **`ChunkingStrategy._normalize_doc_args(doc_or_text, doc_id)`:** Polymorphic helper normalizing `LoadedDocument` objects or raw `str` text into `(text, doc_id)` tuples.
- **`ChunkingStrategy.chunk(doc_or_text, doc_id) -> list[Chunk]`:** Abstract method defining text slicing contract returning list of typed `Chunk` domain objects.
- **`BaseChunker = ChunkingStrategy`:** Backward-compatible alias mapping.
- **`FixedSizeChunker(ChunkingStrategy)`:** Concrete strategy splitting document text using exact token count sliding windows (`chunk_size` and `overlap`) from the injected tokenizer with dual-mode token ID / binary-search execution and orphan block detection.
- **`RecursiveStructuralChunker(ChunkingStrategy)`:** Concrete strategy recursively splitting text along hierarchical structural boundaries (`\n# `, `\n## `, `\n### `, `\n\n`, `\n`, `. `, ` `) with exact token counting from the injected tokenizer.
- **`RecursiveStructuralChunker._partition_text(text, start, end, separators)`:** Recursively partitions a text range `[start:end]` into spans fitting within `chunk_size` tokens based on delimiter hierarchy.
- **`RecursiveStructuralChunker._fallback_spans(text, start, end)`:** Character binary search fallback for text spans exceeding `chunk_size` when no structural delimiters fit.

### Tokenizer & Chunking Engine Unit Tests

#### `tests/unit/test_tokenizers.py`
- **`test_base_tokenizer_abc_instantiation()`:** Verifies `BaseTokenizer` ABC cannot be directly instantiated.
- **`test_tiktoken_encoder()`:** Validates `TiktokenEncoder` encoding, decoding, and count calculation.
- **`test_gemini_encoder()`:** Validates `GeminiEncoder` count calculations and SentencePiece fallback handling.
- **`test_heuristic_tokenizer()`:** Validates `HeuristicTokenizer` token estimation and bounds validation.
- **`test_get_tokenizer_factory()`:** Tests factory routing by provider name (`gemini`, `tiktoken`, `heuristic`).

#### `tests/unit/test_chunkers.py`
- **`test_chunker_with_injected_gemini_encoder()`:** Verifies `FixedSizeChunker` and `RecursiveStructuralChunker` operate seamlessly with injected `GeminiEncoder`.
- **`test_chunking_strategy_parameter_validations()`:** Validates numeric parameter boundary checks for `chunk_size`, `overlap`, and `min_chunk_size`.
- **`test_chunking_strategy_raw_string_input()`:** Verifies string inputs with custom `doc_id` chunk successfully without `LoadedDocument` wrappers.
- **`test_chunking_strategy_inheritance()`:** Confirms `FixedSizeChunker` and `RecursiveStructuralChunker` inherit from `ChunkingStrategy`.
- **`test_fixed_size_chunker()`:** Validates fixed chunking window boundaries, overlap offsets, and token counting.
- **`test_recursive_chunker()`:** Validates recursive chunking structural boundary preservation, orphan block avoidance, and token counting.
- **`test_fixed_size_token_chunker_exact_counts()`:** Validates exact token limits and sliding window overlap offsets using `TiktokenEncoder`.
- **`test_fixed_size_token_chunker_empty_input()`:** Verifies `FixedSizeChunker` handles empty strings cleanly returning empty chunk list.
- **`test_fixed_size_token_chunker_orphan_detection()`:** Verifies orphan block detection flags chunks that split Markdown tables.
- **`test_recursive_structural_chunker_custom_separators()`:** Verifies `RecursiveStructuralChunker` respects custom separator lists.
- **`test_recursive_structural_chunker_empty_input()`:** Verifies `RecursiveStructuralChunker` returns an empty list for empty strings.
- **`test_recursive_structural_chunker_markdown_hierarchy()`:** Validates `RecursiveStructuralChunker` preserves Markdown title, section, and subsection structural boundaries.


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
- **`test_loader_structural_shielding_integration()`:** Verifies loading Markdown fixtures containing tables and code blocks preserves exact formatting after cleaning.

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

#### `src/ingestion/detector.py`
- **`StructuralBlock`:** Immutable NamedTuple recording `block_type`, `start_char`, `end_char`, and block string `content`.
- **`OrphanBlockDetector.__init__()`:** Initializes regex patterns for Markdown pipe tables (`(?:^|\n)(\|[^\n]+\|\n?)+`), fenced code blocks (``` and ~~~), and math blocks (`$$`).
- **`OrphanBlockDetector.extract_structural_blocks(text: str) -> list[StructuralBlock]`:** Scans source text and extracts structural block instances with exact character start and end index spans.
- **`OrphanBlockDetector.detect_orphan_blocks(cleaned_text: str, chunks: list[Chunk]) -> int`:** Finds all structural blocks, checks chunk intersection and single-chunk full enclosure (`c.start_char <= block.start_char and c.end_char >= block.end_char`), and returns the total count of severed orphan blocks.
- **`OrphanBlockDetector.is_orphan_chunk(chunk: Chunk, cleaned_text: str) -> bool`:** Determines whether a specific chunk contains a severed fragment of a structural element.

#### `src/ingestion/monitor.py`
- **`IngestionMonitor(__init__)`:** Configures threshold boundaries for `min_chunk_size` (default 20), `max_overlap_tolerance` (default 0.05), `coverage_threshold` (default 0.98), and optional injected `BaseTokenizer`, instantiating `OrphanBlockDetector`.
- **`IngestionMonitor._detect_orphan_blocks(cleaned_text: str, chunks: list[Chunk]) -> int`:** Delegates structural block scanning to `OrphanBlockDetector.detect_orphan_blocks()`.
- **`IngestionMonitor._compute_token_delta(cleaned_text: str, chunks: list[Chunk], source_tokens: int | None) -> int`:** Calculates net non-overlapping chunk tokens by subtracting overlap token counts and computes source token delta.
- **`IngestionMonitor.audit_document(document_id, source_path, cleaned_text, chunks, errors, source_tokens) -> DocumentReport`:** Audits a single document, calculating unique character coverage set, duplicate character ratio, orphan block count, token count delta, undersized chunk ratio, and status (`"ok"`, `"warning"`, `"error"`).
- **`IngestionMonitor.audit(docs, chunks, strategy_name, errors) -> AuditReport`:** Evaluates retention metrics and orphan counts across a collection of documents, returning an `AuditReport` with global `IngestionMetrics`.
- **`IngestionMonitor.create_ingestion_report(corpus_path, strategy_used, doc_reports) -> IngestionReport`:** Aggregates per-document audit reports into a structured `IngestionReport` deliverable with overall status and blocking alert flags.

#### `tests/unit/test_detector.py`
- **`test_extract_structural_blocks()`:** Verifies regex extraction of table, code block, and math block character spans.
- **`test_orphan_block_detector_table_split()`:** Validates that Markdown tables split across chunk boundaries return `orphan_count == 1`.
- **`test_orphan_block_detector_table_intact()`:** Validates that tables fully enclosed in a single chunk return `orphan_count == 0`.
- **`test_orphan_block_detector_code_block_split()`:** Ensures fenced code blocks severed mid-function are flagged as orphan blocks.
- **`test_is_orphan_chunk()`:** Verifies `is_orphan_chunk` identifies individual chunks containing severed structural fragments.
- **`test_orphan_detector_empty_and_edge_cases()`:** Ensures detector handles empty input text or empty chunk lists gracefully.

#### `tests/unit/test_monitor.py`
- **`test_ingestion_monitor_pass()`:** Verifies monitor produces PASSED status when character coverage ratio $\ge 0.98$ and zero orphan blocks exist.
- **`test_ingestion_monitor_low_coverage_warning()`:** Verifies monitor flags low coverage (< 98%) with FAILED audit status and warning document status.
- **`test_ingestion_monitor_orphan_detection()`:** Verifies orphan Markdown tables split across chunk boundaries trigger error status.
- **`test_audit_document_empty_and_errors()`:** Tests `audit_document` behavior on empty document strings and explicitly passed error lists.
- **`test_duplicate_char_ratio_calculation()`:** Validates duplicate character ratio computation for overlapping chunk spans.
- **`test_create_ingestion_report()`:** Validates creation and aggregation of structured `IngestionReport` objects.
- **`test_token_count_delta_computation_exact()`:** Verifies exact token count delta calculation accounting for chunk overlaps.
- **`test_undersized_chunks_ratio_calculation()`:** Validates undersized chunk ratio computation against `min_chunk_size`.
- **`test_create_ingestion_report_with_blocking_alerts()`:** Verifies `IngestionReport` correctly sets `has_blocking_alerts` when error documents exist.

### Pipeline Orchestrator Facade

#### `src/ingestion/pipeline.py`
- **`PipelineResult`:** Frozen `@dataclass` bundling `audit_report` (`AuditReport`), `ingestion_report` (`IngestionReport`), `documents` (`list[Document]`), `chunks` (`list[Chunk]`), and `doc_reports` (`list[DocumentReport]`) as unified pipeline output.
- **`_build_chunker(config: IngestionConfig) -> BaseChunker`:** Module-level factory selecting `FixedSizeChunker` or `RecursiveStructuralChunker` based on `config.strategy` enum, injecting `config.tokenizer` name into the chunker.
- **`_discover_files(input_path: Path) -> list[Path]`:** Sorted recursive glob returning all regular files under the input directory for deterministic processing order.
- **`PipelineOrchestrator.__init__(config: IngestionConfig | None = None)`:** Initializes `TextCleaner`, `BaseChunker` (via `_build_chunker`), and `IngestionMonitor` (with `coverage_threshold` from config).
- **`PipelineOrchestrator.config -> IngestionConfig`:** Read-only property exposing the pipeline configuration.
- **`PipelineOrchestrator.run(input_dir, output_dir, report_path) -> PipelineResult`:** Entry point executing full pipeline: resolves paths from config defaults, discovers files, processes corpus, exports JSONL chunks and audit report, creates `IngestionReport`, and returns `PipelineResult`.
- **`PipelineOrchestrator._process_corpus(input_path) -> tuple[list[Document], list[Chunk], list[DocumentReport]]`:** Iterates all files through `_process_single_file`, collecting documents, chunks, and per-document reports.
- **`PipelineOrchestrator._process_single_file(file_path) -> tuple[Document | None, list[Chunk], DocumentReport]`:** Processes one file through Load → Clean → Chunk → Audit stages with per-stage exception shielding via `FileShieldContext`. Each sub-stage is independently wrapped so failures record tracebacks into `DocumentReport.errors` without crashing the batch.
- **`PipelineOrchestrator._shield_load(file_path, ctx) -> DocumentLoader | None`:** Shield wrapper resolving the loader for a file extension; records `IngestionStage.LOAD` error on failure.
- **`PipelineOrchestrator._shield_read(loader, file_path, ctx) -> LoadedDocument | None`:** Shield wrapper reading raw document content from disk; records `IngestionStage.LOAD` error on failure.
- **`PipelineOrchestrator._shield_clean(raw_content, file_path, ctx) -> str | None`:** Shield wrapper running text cleaner; records `IngestionStage.CLEAN` error on failure.
- **`PipelineOrchestrator._shield_chunk(doc, file_path, ctx) -> list[Chunk] | None`:** Shield wrapper running chunker; records `IngestionStage.CHUNK` error on failure.
- **`PipelineOrchestrator._shield_audit(doc, file_chunks, ctx) -> DocumentReport`:** Shield wrapper running monitor audit; falls back to error report on `IngestionStage.AUDIT` failure.
- **`PipelineOrchestrator._error_report(file_path, ctx) -> DocumentReport`:** Constructs error `DocumentReport` from accumulated `FileShieldContext` error messages with `status="error"`.
- **`PipelineOrchestrator._log_summary(docs, chunks, report)`:** Emits structured log entry with document count, chunk count, coverage ratio, and audit status.
- **`IngestionPipeline`:** Backward-compatible wrapper converting raw constructor arguments (`strategy_name`, `chunk_size`, `overlap`, `min_chunk_size`) into `IngestionConfig` and delegating to `PipelineOrchestrator`. Returns legacy `AuditReport` from `run()` for CLI compatibility.

#### `tests/unit/test_pipeline.py`
- **`test_build_chunker_fixed()`:** Verifies fixed strategy config produces `FixedSizeChunker`.
- **`test_build_chunker_recursive_default()`:** Verifies default config produces `RecursiveStructuralChunker`.
- **`test_discover_files_empty_dir()`:** Verifies empty directory returns no files.
- **`test_discover_files_recursive()`:** Verifies recursive file discovery under nested directories.
- **`test_pipeline_result_immutable()`:** Verifies `PipelineResult` frozen dataclass rejects field mutation.
- **`test_orchestrator_default_config()`:** Verifies orchestrator initializes with default `IngestionConfig`.
- **`test_orchestrator_custom_config()`:** Verifies orchestrator accepts custom `IngestionConfig`.
- **`test_orchestrator_run_with_fixtures()`:** Verifies full orchestrator run produces output files and valid `PipelineResult`.
- **`test_orchestrator_ingestion_report_populated()`:** Verifies `IngestionReport` is populated with per-document details.
- **`test_orchestrator_skips_unsupported_files()`:** Verifies orchestrator emits error `DocumentReport` for unsupported file types without crashing.
- **`test_orchestrator_empty_corpus()`:** Verifies orchestrator handles empty input directory gracefully.
- **`test_orchestrator_fixed_strategy()`:** Verifies orchestrator works with fixed chunking strategy.
- **`test_error_report_structure()`:** Verifies `_error_report` produces valid `DocumentReport` with error status using `FileShieldContext`.
- **`test_legacy_pipeline_returns_audit_report()`:** Verifies `IngestionPipeline` backward-compat returns `AuditReport`.
- **`test_legacy_pipeline_fixed_strategy()`:** Verifies `IngestionPipeline` wrapper works with fixed strategy.

### File-Level Exception Shielding

#### `src/ingestion/file_shield.py`
- **`IngestionStage(str, Enum)`:** Named pipeline processing stages (`LOAD`, `CLEAN`, `CHUNK`, `AUDIT`) used to tag errors to their origin.
- **`StageError`:** Frozen dataclass capturing a single stage failure: `stage` (`IngestionStage`), `error_type` (exception class name), `message` (exception string), and `traceback` (full `traceback.format_exception()` output).
- **`StageError.format_short() -> str`:** Formats concise single-line error summary as `[stage] ErrorType: message`.
- **`FileShieldContext`:** Per-file mutable accumulator collecting `StageError` objects from each processing stage.
- **`FileShieldContext.record_error(stage, exc)`:** Captures exception with full traceback via `traceback.format_exception()` and emits structured log warning.
- **`FileShieldContext.has_errors -> bool`:** Property checking if any stage recorded an error.
- **`FileShieldContext.failed_stages -> list[IngestionStage]`:** Property returning the list of stages that failed.
- **`FileShieldContext.format_error_messages() -> list[str]`:** Formats all errors as short `[stage] ErrorType: message` strings for `DocumentReport.errors`.
- **`FileShieldContext.format_tracebacks() -> list[str]`:** Returns full traceback strings for post-mortem diagnostics.

#### `tests/unit/test_file_shield.py`
- **`test_stage_enum_values()`:** Verifies all four pipeline stages are defined with correct string values.
- **`test_stage_error_frozen()`:** Verifies `StageError` is immutable (rejects field mutation).
- **`test_stage_error_format_short()`:** Verifies `format_short()` produces concise `[stage] ErrorType: message` string.
- **`test_context_no_errors()`:** Verifies fresh `FileShieldContext` has no errors and empty formatted output.
- **`test_context_record_error_captures_traceback()`:** Verifies `record_error()` captures exception traceback string with `Traceback` header.
- **`test_context_multiple_errors()`:** Verifies context accumulates errors from multiple stages and reports correct `failed_stages`.
- **`test_context_format_tracebacks()`:** Verifies `format_tracebacks()` returns full traceback strings.
- **`test_shield_load_unsupported_format()`:** Verifies `_shield_load` records `LOAD` error for unsupported file type.
- **`test_shield_read_missing_file()`:** Verifies `_shield_read` records `LOAD` error for missing file.
- **`test_shield_clean_error()`:** Verifies `_shield_clean` records `CLEAN` error on cleaner failure.
- **`test_shield_chunk_error()`:** Verifies `_shield_chunk` records `CHUNK` error on chunker failure.
- **`test_shield_audit_error_returns_error_report()`:** Verifies `_shield_audit` returns error `DocumentReport` on monitor failure.
- **`test_batch_continues_after_file_error()`:** Verifies batch run continues processing valid files after one file fails.
- **`test_traceback_preserved_in_error_report()`:** Verifies traceback info propagates through `FileShieldContext` to `DocumentReport.errors`.

### JSONL & Audit Report Exporters

#### `src/ingestion/exporters.py`
- **`BaseExporter(ABC, Generic[T])`:** Abstract base class defining uniform `export(data: T, output_path: str | Path) -> Path` contract for all serialization exporters.
- **`JSONLChunkExporter(BaseExporter[list[Chunk]])`:** Concrete exporter serializing `Chunk` domain models to JSON Lines (`.jsonl`) format with batch `export()`, streaming `export_stream()`, and round-trip `read()` validation.
- **`AuditReportExporter(BaseExporter[BaseDomainModel])`:** Concrete exporter serializing `AuditReport` or `IngestionReport` models to formatted JSON (`indent=2`) with `export()`, `read_audit_report()`, and `read_ingestion_report()`.
- **`export_chunks_jsonl(chunks, output_path) -> Path`:** Procedural helper function delegating to `JSONLChunkExporter().export()`.
- **`export_audit_report(report, output_path) -> Path`:** Procedural helper function delegating to `AuditReportExporter().export()`.

#### `tests/unit/test_exporters.py`
- **`test_jsonl_chunk_exporter_export_and_read()`:** Verifies `JSONLChunkExporter` batch export and `read()` deserialization accuracy.
- **`test_jsonl_chunk_exporter_stream()`:** Verifies `export_stream()` line-by-line generator streaming to JSONL.
- **`test_jsonl_chunk_exporter_missing_file()`:** Ensures `AuditError` is raised when reading non-existent JSONL files.
- **`test_audit_report_exporter_audit_report()`:** Validates `AuditReportExporter` formatting and `read_audit_report()` deserialization.
- **`test_audit_report_exporter_ingestion_report()`:** Validates `AuditReportExporter` formatting and `read_ingestion_report()` deserialization.
- **`test_audit_report_exporter_missing_files()`:** Ensures `AuditError` is raised when reading missing JSON report files.
- **`test_procedural_export_helpers()`:** Tests `export_chunks_jsonl` and `export_audit_report` procedural helper functions.

### Typer CLI Commands, Rich Console UI & Gatekeeper

#### `src/ingestion/gatekeeper.py`
- **`ExitCodeGatekeeper`:** Evaluates `PipelineResult` quality metrics against thresholds to determine process exit code for CI/CD builds.
  - **`evaluate(result) -> int`:** Returns exit code `0` if quality gates pass, `1` if blocking alerts exist.
  - **`should_exit(result) -> bool`:** Evaluates `has_blocking_alerts`, audit status (`PASSED`/`FAILED`), document errors count, and character coverage threshold.
  - **`get_blocking_reasons(result) -> list[str]`:** Collects human-readable failure explanations (orphan block counts, processing errors, low coverage percentage) for terminal formatting.

#### `src/ingestion/console.py`
- **`RichConsoleRenderer`:** Formatter class encapsulating Rich panel and table rendering logic for CLI terminal output.
  - **`render_header(strategy, input_dir) -> Panel`:** Constructs colorful launch status panel with active strategy and input directory.
  - **`render_document_table(doc_reports) -> Table`:** Constructs per-file audit status table displaying filename, chunk count, coverage percentage, orphan block count, token delta, and status tag with conditional color formatting (green/yellow/red).
  - **`render_summary_table(audit_report, ingestion_report) -> Table`:** Constructs global audit metric summary table displaying input docs, total output chunks, coverage ratio, orphan count, documents in error, and overall status.
  - **`render_pipeline_result(result) -> None`:** Executes complete output rendering pass displaying breakdown and summary tables to console.

#### `src/ingestion/cli.py`
- **`app`:** Main `typer.Typer` application instance registered as CLI entrypoint `ingest`.
- **`run(...)`:** Main CLI command handling options (`--input`, `--output`, `--strategy`, `--chunk-size`, `--overlap`, `--min-chunk-size`, `--report`), instantiating `PipelineOrchestrator`, delegating rendering to `RichConsoleRenderer`, and enforcing exit code quality gates via `ExitCodeGatekeeper` (`code=1`).

#### `tests/unit/test_gatekeeper.py`
- **`test_gatekeeper_pass_clean_result()`:** Verifies clean pipeline result returns exit code 0 and empty blocking reasons list.
- **`test_gatekeeper_fail_has_blocking_alerts()`:** Confirms `has_blocking_alerts=True` returns exit code 1.
- **`test_gatekeeper_fail_audit_metrics_status_failed()`:** Validates status `FAILED` triggers gate failure.
- **`test_gatekeeper_fail_documents_in_error()`:** Ensures processing errors produce non-zero exit code and explicit reason.
- **`test_gatekeeper_fail_orphan_blocks()`:** Validates orphaned Markdown table or code block detection returns exit code 1.
- **`test_gatekeeper_fail_low_coverage()`:** Verifies coverage dropping below threshold triggers exit code 1.
- **`test_gatekeeper_generic_blocking_fallback()`:** Tests fallback message when generic blocking alert flag is set.

#### `tests/unit/test_console.py`
- **`test_render_header()`:** Verifies header panel contains pipeline title and active strategy parameters.
- **`test_render_document_table()`:** Verifies per-file audit breakdown table header columns and document data rendering.
- **`test_render_summary_table()`:** Verifies global aggregate audit metrics table formatting and values.
- **`test_render_pipeline_result_output()`:** Verifies console result output capturing rendered breakdown and summary tables.

#### `tests/unit/test_cli.py`
- **`test_cli_help()`:** Verifies `CliRunner` invocation with `--help` renders all option flags and documentation.
- **`test_cli_run_success()`:** Verifies successful pipeline execution with default CLI options over test corpus fixtures.
- **`test_cli_run_custom_parameters()`:** Verifies CLI execution with explicit strategy and chunking option overrides.
- **`test_cli_invalid_strategy()`:** Ensures invalid strategy options raise `IngestionError` and exit with non-zero code 1.
- **`test_cli_empty_directory()`:** Confirms CLI handles empty input directories cleanly without errors.
- **`test_cli_gatekeeper_exit_code_1_on_fixed_strategy_table_split()`:** Confirms CLI gatekeeper exits with code 1 when fixed chunking strategy splits Markdown table blocks.
- **`test_cli_gatekeeper_exit_code_0_on_recursive_strategy()`:** Confirms CLI gatekeeper exits with code 0 on recursive structural chunking.

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

### Synthetic Test Corpus Engine

#### `src/ingestion/corpus.py`
- **`SyntheticFixtureSpec(BaseDomainModel)`:** Immutable Pydantic domain model defining fixture metadata (`name`, `category`, `description`, `expected_behavior`, `file_path`).
- **`SyntheticCorpus(BaseDomainModel)`:** Domain manager class providing `list_fixtures()`, `get_fixture_path()`, `load_fixture_content()`, `ensure_default_fixtures()`, and `validate_corpus()`.
- **`DEFAULT_FIXTURES`:** Immutable constant dictionary containing default benchmark document definitions (`01_clean_doc.md`, `02_noisy_header.txt`, `03_table_split.md`, `04_corrupted_encoding.txt`).

#### `tests/unit/test_corpus.py`
- **`test_synthetic_fixture_spec_model()`:** Validates model instantiation and property defaults.
- **`test_synthetic_corpus_list_fixtures()`:** Confirms `list_fixtures()` returns metadata for all 4 benchmark files.
- **`test_synthetic_corpus_get_fixture_path()`:** Verifies automatic creation and path retrieval for named fixtures.
- **`test_synthetic_corpus_unknown_fixture_raises_error()`:** Confirms `DocumentLoadError` is raised for unknown fixture names.
- **`test_synthetic_corpus_load_fixture_content()`:** Validates string content reading for test fixtures.
- **`test_synthetic_corpus_validate_corpus()`:** Confirms integrity check returns `True` for all active benchmark files.
- **`test_default_fixtures_dictionary_completeness()`:** Verifies `DEFAULT_FIXTURES` includes all mandatory roadmap files and schema keys.

### Comparative Strategy Benchmark Engine

#### `src/ingestion/benchmark.py`
- **`BenchmarkStrategyMetrics(BaseDomainModel)`:** Immutable Pydantic domain model holding execution time, token/char averages, coverage ratios, orphan block counts, token deltas, and audit status for a strategy.
- **`BenchmarkComparisonResult(BaseDomainModel)`:** Immutable Pydantic domain model storing dual strategy metrics, coverage delta, orphan reduction count, chunk count differences, and winning strategy recommendation.
- **`StrategyBenchmarkRunner`:** Benchmark runner executing dual `PipelineOrchestrator` runs over target corpus directories, computing comparison metrics, determining the winning strategy, and rendering GitHub Markdown summary tables.

#### `tests/unit/test_benchmark.py`
- **`test_benchmark_models_immutability()`:** Verifies `BenchmarkStrategyMetrics` and `BenchmarkComparisonResult` model instantiation, immutability, and attribute integrity.
- **`test_strategy_benchmark_runner_execution()`:** Confirms `StrategyBenchmarkRunner` executes dual strategy comparison over corpus fixtures and determines `winning_strategy`.
- **`test_format_markdown_table()`:** Verifies `format_markdown_table()` outputs expected GitHub Markdown comparative table layout.
- **`test_benchmark_cli_command()`:** Confirms Typer CLI `benchmark` subcommand and `--benchmark` option execute cleanly and print summary tables.

---

## 📦 3. Manifest & Automation

- **`ruff.toml`:** Dedicated Ruff static linter and formatter configuration (rules E, W, F, I, B, UP, SIM, RUF).
- **`pyproject.toml`:** Dependency declarations (Poetry), CLI scripts, MyPy strict options, Pytest coverage rules.
- **`Makefile`:** Shortcuts (`make install`, `make lint`, `make test`, `make dev`, `make clean`, `make docker-build`).
- **`Dockerfile`:** Multi-stage production container image specification.

