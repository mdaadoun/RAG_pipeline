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

