# Technical Glossary

> **Scope:** Shared definitions for software architecture, telemetry, RAG document ingestion, and information loss auditing.

---

## 🛠️ 1. Software & Architecture Patterns

### Environment Initialization
Provisioning deterministic, isolated runtime dependencies, locked configurations, and environment setting singletons.

### Structured Logging
Format for log records using standardized key-value JSON fields (timestamp, level, event context) to streamline automated log analysis.

### Static Type Guarding
Compile-time static analysis using Mypy strict mode to enforce type constraints and eliminate runtime reference errors.

### Static Code Analysis
Automated examination of source code before execution to detect syntax errors, security vulnerabilities, and style violations.

### Strict Type Checking
Compiler/type-checker mode that requires explicit type signatures on all functions, classes, and variables, forbidding dynamic implicit types.

### AST Linting
Analyzing the Abstract Syntax Tree of source code to detect logical antipatterns and dead code fast without executing runtime code.

### Quality Gate
Automated checkpoint in CI/CD pipelines that blocks code merge/deployment if linters, type checkers, or test suites fail.

### Fail-Fast Validation
Validating environment variables and configuration schemas at application startup before running downstream workloads.

### Package Hierarchy
Structured python package layout separating data contracts, loaders, transformations, chunkers, quality audit monitors, and CLI presentation.

### Custom Exception Hierarchy
Object-oriented error classification allowing granular error catching (e.g. `DocumentLoadError`, `ChunkError`) while maintaining a single root exception (`IngestionError`).

### IngestionError
Base exception class for all document ingestion pipeline errors equipped with message strings, structured details dictionary payloads, and JSON serialization (`to_dict()`).

### DocumentLoadError
Subclass of `IngestionError` raised when loading, reading, or parsing a source document fails.

### CleanError
Subclass of `IngestionError` raised when text cleaning, normalization, or header/footer stripping encounters an error.

### ChunkError
Subclass of `IngestionError` raised during document text chunking or token boundary splitting operations.

### AuditError
Subclass of `IngestionError` raised when quality audit checks or safety thresholds (such as character coverage ratio) fail.

### Polymorphic Error Handling
Software design pattern where callers catch multiple stage-specific exceptions using their common base class (`IngestionError`).

### Test Runner Registration
Structuring tests into standard Pytest module hierarchies (`tests/unit/`, `tests/integration/`) for automated discovery and execution in test runners.

### BaseDomainModel
Abstract immutable root Pydantic V2 model configuring frozen state (`frozen=True`) and forbidding extra fields (`extra="forbid"`) across all domain schemas.

### StrategyType
String-backed enumeration specifying valid document chunking strategies (`FIXED = "fixed"` or `RECURSIVE = "recursive"`).

### IngestionConfig
Domain model encapsulating chunking, coverage threshold, and directory path configuration with value validations.

### LoadedDocument
Immutable domain representation of a raw loaded source document, including content, file path, and calculated character/token properties.

### DocumentReport
Per-document structural audit report encapsulating character coverage, duplicate character ratios, and orphan block counts.

### IngestionReport
Global structured audit report deliverable recording total chunks, global character coverage, and blocking alerts.

---

## 🤖 2. RAG Ingestion & Document Processing

### Tokenization & BPE Encoding
Converting raw text strings into discrete integer token sequences using byte-pair encoding dictionaries (`tiktoken` `cl100k_base`).

### Structural Protection Shielding
Regex-based masking of Markdown tables and code blocks during text cleaning to prevent structural truncation.

### Information Loss Audit
Systematic measurement of document retention, character coverage ratios, duplicate overlaps, and orphan split blocks post-chunking.

### DocumentLoader
Abstract base class defining contract interface for file ingestion loaders returning typed domain model `LoadedDocument`.

### TextMarkdownLoader
Unified document loader supporting auto-detection and parsing of plain text and markdown format files.

### Deterministic SHA-256 Document Identifier
Unique 16-char identifier generated from a SHA-256 digest of file name and content string to ensure idempotent indexing across pipeline executions.

### DocumentLoadError Shielding
Encapsulation pattern translating low-level OS and decoding errors into domain-specific exception models carrying structured metadata payloads.

### NFKC Normalization
Normalization Form KC (Compatibility Decomposition followed by Canonical Composition) standardizing unicode compatibility characters and ligatures into canonical equivalents.

### Boilerplate Line Deduplication
Filtering algorithm removing identical non-empty lines that repeat more than N times across document content to reduce token noise.

### UUID-Prefixed Placeholder Token
A unique token format (`___SHIELDED_<uuid>_<idx>___`) inserted in place of protected text regions to guarantee zero collision with document contents.

### Table Pipe Regex Shielding
Regular expression matching pattern (`^\|.*\|$) that detects contiguous rows of Markdown pipe-delimited tabular data.

### BaseTokenizer
Abstract base class contract defining model-agnostic token encoding, decoding, and counting signatures.

### GeminiEncoder
Tokenizer adapter encapsulating Google Gemini API tokenization with calibrated SentencePiece offline fallback.

### TiktokenEncoder
Domain adapter wrapper encapsulating OpenAI tiktoken library for encoding, decoding, and token counting.

### ChunkingStrategy
Abstract base class defining the standard interface and injected token encoder for document chunking algorithms.

### Model-Agnostic Tokenization
Architectural decoupling strategy separating document chunkers from specific LLM provider tokenizers, enabling dynamic swapping between OpenAI, Gemini, or custom encoders.

### cl100k_base
Byte-pair encoding (BPE) tokenization scheme used by OpenAI models (e.g. GPT-4, text-embedding-ada-002).

### Token Windowing
Document segmentation technique partitioning text according to exact BPE or SentencePiece token counts rather than raw character lengths.

### Fixed-Size Token Chunker
A document chunking strategy that partitions text into windows of fixed token length (`chunk_size`) with fixed token overlap (`overlap`) using an injected tokenizer.

### Token Sliding Window
An iterative algorithm that advances a window frame over a sequence of tokens by `step_tokens = chunk_size - overlap` to produce overlapping document segments.

### Orphan Block
A structural Markdown element (such as a table or code block) whose contents are partially severed across chunk boundaries, causing semantic context loss.

### RecursiveStructuralChunker
A context-aware document segmentation strategy that recursively splits text across structural delimiters (headers, paragraphs, lines, sentences) while respecting model token bounds.

### Hierarchical Separator Fallback
An ordered sequence of structural delimiters evaluated sequentially to partition text into the largest valid sub-blocks fitting within max token constraints.

### Leaf Span Partitioning
The process of recursively breaking text down into contiguous atomic character ranges `[start_char, end_char]` prior to token-bounded candidate chunk merging.

### Orphan Block Flag
A boolean property (`is_orphan_block`) indicating whether a chunk boundary cuts through a protected structural element like a Markdown table or code block.

### Character Coverage Ratio (`char_coverage_ratio`)
The ratio of unique source document characters present in at least one generated chunk divided by the total character count of the cleaned text.

### Duplicate Character Ratio (`duplicate_char_ratio`)
The proportion of extra character occurrences across generated chunks resulting from configured chunk overlap or duplicate segmentation.

### Token Delta (`token_count_delta`)
The difference between total source document tokens and aggregate tokens across generated chunks.

### Undersized Chunk
A chunk whose total token or character count falls below a specified minimum threshold.

### Orphan Block
A Markdown structural entity (table, code block, math block) split across chunk boundaries such that no single chunk contains the complete block.

### Structural Block Range
The exact character start and end index span (`[start_char, end_char]`) of a contiguous structural element within cleaned text.

### Block Preservation
The condition where at least one generated chunk entirely spans a structural block range without boundary truncation.

### Overlap Compensation
Audit technique that subtracts token counts of overlapping character regions between consecutive chunks to prevent false expansion metrics during token loss audit.

### Undersized Chunks Ratio (`undersized_chunks_ratio`)
The proportion of generated document chunks whose token count is lower than configured minimum chunk size threshold (`min_chunk_size`).

---

## 🔧 3. Pipeline Orchestration & Facade

### PipelineOrchestrator
Facade class coordinating all ingestion stages (Loaders → Cleaner → Chunkers → Monitor → Exporters) via a single typed `IngestionConfig`, returning an immutable `PipelineResult`.

### PipelineResult
Immutable frozen dataclass returned by `PipelineOrchestrator.run()`, bundling `audit_report`, `ingestion_report`, `documents`, `chunks`, and `doc_reports` as unified pipeline output.

### Facade Pattern
Structural design pattern providing a simplified interface to a complex subsystem of classes (here: loaders, cleaner, chunkers, monitor, exporters) behind a single entry point.

### `_build_chunker`
Module-level factory function selecting and instantiating the correct `ChunkingStrategy` subclass (`FixedSizeChunker` or `RecursiveStructuralChunker`) with tokenizer injection based on `IngestionConfig.strategy` and `IngestionConfig.tokenizer` enum values.

### `_discover_files`
Module-level helper performing sorted recursive glob over an input directory, returning all regular files for deterministic processing order.

### Dual Report Model
Architecture pattern where the pipeline simultaneously produces a legacy `AuditReport` (aggregate corpus metrics for CLI pass/fail gating) and a detailed `IngestionReport` (per-document `DocumentReport` list for diagnostics and UI rendering).

### FileShieldContext
Per-file mutable accumulator that collects `StageError` objects from each processing stage, providing error formatting and traceback retrieval.

### StageError
Frozen dataclass capturing a single stage failure: stage name, exception type, message, and full traceback string.

### IngestionStage
Enum of named pipeline processing stages (`LOAD`, `CLEAN`, `CHUNK`, `AUDIT`) used to tag errors to their origin.

### Exception Shielding
Design pattern where each sub-operation is wrapped in its own `try/except` block to prevent one failure from cascading and crashing the entire batch.

### JSONL (JSON Lines)
A streamable text format where each line is a valid JSON object, optimized for line-by-line parsing, vector database ingestion, and large dataset chunking.

### JSONLChunkExporter
Exporter module responsible for serializing `Chunk` domain models into UTF-8 encoded JSON Lines files with automatic parent directory creation.

### AuditReportExporter
Exporter module responsible for formatting and serializing `AuditReport` and `IngestionReport` domain models into indented JSON files.

### Round-trip Deserialization
The process of reading exported JSON/JSONL artifacts back into strongly typed Pydantic domain models to verify serialization losslessness and schema adherence.

### Typer CLI
A modern Python library for building command line interface applications based on Python type hints.

### Annotated Metadata
Python typing construct (`typing.Annotated`) used by Typer to attach CLI option flags, short aliases, and help docstrings to function parameters.

### Quality Gate Exit Code
Non-zero exit code (`1`) raised via `typer.Exit` when ingestion audit status fails, enabling CI/CD pipeline blocking.

### Rich Console Renderer
A dedicated presentation component leveraging the Rich library to format structured domain reports into visually rich status tables and panels.

### Per-Document Breakdown Table
A tabular terminal visualizer detailing per-file document coverage, chunk counts, orphan block counts, token deltas, and status indicators.

### Conditional Style Formatting
Dynamic terminal text styling where cell colors (green, yellow, red) automatically adapt based on threshold bounds of metrics like character coverage or orphan counts.

### Exit Code Gatekeeper
Automated pipeline evaluation mechanism that returns process exit code `0` on quality pass or non-zero code `1` on blocking alerts to control CI/CD execution status.

### Quality Gate
Pre-defined numerical or structural criteria (e.g. 98% coverage threshold, zero orphan blocks, zero document load errors) required for corpus ingestion approval.

### Blocking Alert
Critical data quality failure condition such as fragmented markdown tables or parsing exceptions that invalidates RAG corpus validity.
