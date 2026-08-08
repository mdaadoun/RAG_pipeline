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

### Test Runner Registration
Structuring tests into standard Pytest module hierarchies (`tests/unit/`, `tests/integration/`) for automated discovery and execution in test runners.

---

## 🤖 2. RAG Ingestion & Document Processing

### Tokenization & BPE Encoding
Converting raw text strings into discrete integer token sequences using byte-pair encoding dictionaries (`tiktoken` `cl100k_base`).

### Structural Protection Shielding
Regex-based masking of Markdown tables and code blocks during text cleaning to prevent structural truncation.

### Information Loss Audit
Systematic measurement of document retention, character coverage ratios, duplicate overlaps, and orphan split blocks post-chunking.
