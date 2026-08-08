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

### Fail-Fast Validation
Validating environment variables and configuration schemas at application startup before running downstream workloads.

---

## 🤖 2. RAG Ingestion & Document Processing

### Tokenization & BPE Encoding
Converting raw text strings into discrete integer token sequences using byte-pair encoding dictionaries (`tiktoken` `cl100k_base`).

### Structural Protection Shielding
Regex-based masking of Markdown tables and code blocks during text cleaning to prevent structural truncation.

### Information Loss Audit
Systematic measurement of document retention, character coverage ratios, duplicate overlaps, and orphan split blocks post-chunking.
