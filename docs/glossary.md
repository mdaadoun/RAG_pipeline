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


