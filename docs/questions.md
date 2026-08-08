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

---

### Q4: Why enforce MyPy strict mode in a Python RAG pipeline instead of relying on standard dynamic typing?
**Answer:** RAG pipelines process unstructured text data and pass complex data objects (Documents, Chunks, AuditReports) between loaders, cleaners, chunkers, and monitors. Enforcing MyPy strict mode guarantees interface contracts, prevents NullPointer/AttributeError crashes during batch runs, and documents function signatures explicitly.

---

### Q5: What is the advantage of using Ruff over traditional Python linters like Flake8, Black, and Isort?
**Answer:** Ruff is written in Rust and executes 10-100x faster than traditional Python tools. It unifies linting, import sorting, and code formatting into a single tool with zero-dependency execution, significantly reducing CI run times.

---

### Q6: How does Makefile standardization improve code quality across team environments?
**Answer:** Makefile provides standardized command shortcuts (`make lint`, `make test`) that abstract underlying tooling details. This ensures developer environments match CI/CD runner environments exactly, preventing 'works on my machine' issues.

---

### Q7: Why create a dedicated `exceptions.py` module with a custom exception hierarchy instead of using built-in Python exceptions?
**Answer:** A custom hierarchy rooted at `IngestionError` enables callers and orchestrators to catch subsystem-specific failures (`DocumentLoadError`, `CleanError`, `ChunkError`) without catching unrelated system exceptions. It standardizes error handling across pipeline stages and simplifies logging and audit reporting.

---

### Q8: How does separating `tests/unit/`, `tests/integration/`, and `tests/fixtures/` impact build pipelines and maintainability?
**Answer:** It allows fast, isolated execution of lightweight unit tests during local development while isolating complex multi-component pipeline runs and synthetic test files, facilitating targeted test discovery and clear test reporting.

---

### Q9: Why export core exceptions and models directly from `ingestion.__init__`?
**Answer:** It provides a clean public API contract for external consumers and CLI commands, avoiding deep internal module imports and reducing coupling to internal package layout.

---

### Q10: Why create a custom exception hierarchy rooted at `IngestionError` instead of using standard Python built-in exceptions?
**Answer:** Custom exception hierarchies isolate domain-specific errors from standard runtime errors. It allows pipeline orchestrators to catch any ingestion failure via `except IngestionError:` without catching unrelated system bugs like `KeyError` or `AttributeError`, while enabling stage-specific audit tracking.

---

### Q11: What benefit does the `details` dictionary payload and `to_dict()` method provide to the ingestion pipeline?
**Answer:** The `details` dictionary captures contextual metadata (such as document IDs, invalid characters, or file paths) at the error site. The `to_dict()` method provides a clean dictionary representation for JSON serialization into `DocumentReport` objects and external observability tools.

---

### Q12: How does the exception hierarchy support non-crashing directory batch ingestion?
**Answer:** The batch pipeline orchestrator wraps per-file ingestion stages in `try...except IngestionError as exc:`. Caught exceptions are serialized using `exc.to_dict()` and attached to the file's `DocumentReport.errors` list, allowing batch execution to continue uninterrupted for remaining files.

---

### Q13: Why use Pydantic `ConfigDict(frozen=True, extra="forbid")` for RAG domain models?
**Answer:** Immutability (`frozen=True`) prevents accidental data mutation during text processing pipeline stages, ensuring audit reproducibility. Forbidding extra fields (`extra="forbid"`) catches schema drift, typo bugs, and unexpected API inputs early at the domain boundary.

---

### Q14: How does inheriting from `BaseDomainModel` enforce strict typing and domain integrity?
**Answer:** `BaseDomainModel` centralizes schema configuration, guaranteeing all downstream models (`LoadedDocument`, `Chunk`, `DocumentReport`, `IngestionReport`) inherit identical immutability and strict validation rules without duplicating configuration code across modules.

---

### Q15: How are backward compatibility and domain evolvability achieved when refactoring models?
**Answer:** By creating alias mappings (e.g. `Document = LoadedDocument`) and property getters (e.g. `Chunk.document_id` pointing to `doc_id`), new strict schemas can be introduced without breaking pre-existing code that relies on legacy attribute names.

---

### Q16: Why replace random UUID document identifiers with SHA-256 digest-based identifiers in the document loader?
**Answer:** Random UUIDs introduce non-determinism across pipeline runs, making audit metric tracking, chunk comparisons, and cache deduplication impossible. SHA-256 digests computed over file name and raw text ensure identical input documents produce identical document IDs (`doc_<hash>`), enabling idempotent ingestion and reproducible information loss audits.

---

### Q17: How does the `DocumentLoader` abstraction enforce layer isolation and open-closed principles in the ingestion architecture?
**Answer:** Downstream pipeline modules (cleaners, chunkers, monitors, orchestrators) depend strictly on the abstract `DocumentLoader` interface and domain model `LoadedDocument`. Concrete loaders (`TextLoader`, `MarkdownLoader`, `TextMarkdownLoader`) encapsulate format-specific reading logic. Adding support for new formats (e.g. PDF, HTML) only requires implementing a new loader subclass without modifying downstream code.

---

### Q18: How are file system reading failures and encoding errors handled across the loader boundary?
**Answer:** Low-level file system exceptions like `FileNotFoundError`, `UnicodeDecodeError`, or `OSError` are trapped inside `DocumentLoader._read_content` and `_resolve_path`, then wrapped into `DocumentLoadError`. This preserves exception hierarchy contracts and attaches contextual details (file path, raw error string) for audit logging.

---

### Q19: Why is structural shielding necessary before applying whitespace capping and line deduplication in RAG pipelines?
**Answer:** Without shielding, whitespace normalization and newline capping would destroy code block indentation and break Markdown table row alignment, causing downstream chunkers to split tables mid-row and generate orphan blocks that fail vector retrieval.

---

### Q20: What are the trade-offs of using NFKC normalization instead of standard string stripping alone?
**Answer:** NFKC standardizes compatibility characters like non-breaking spaces (`\xa0`) and ligatures into uniform representations for consistent tokenization and vector embeddings across diverse sources. However, it can transform certain specialized Unicode glyphs if canonical equivalents exist.

---

### Q21: How does `TextCleaner` enforce domain exception shielding for pipeline resilience?
**Answer:** `TextCleaner` validates input types, raises `CleanError` with structured details for invalid inputs, and catches any runtime unexpected failures to wrap them into `CleanError` instances.

---

### Q22: Why use placeholder token substitution instead of line-by-line conditional parsing during text cleaning?
**Answer:** Placeholder token substitution decouples text cleaning operations (NFKC normalization, control byte stripping, whitespace capping, boilerplate deduplication) from block syntax rules. Normalization operations can process the unshielded text cleanly without risking destructive modifications to code block indentation or Markdown table vertical alignments.

---

### Q23: How does the shielding engine handle nested or overlapping protected blocks (e.g. pipe symbols inside fenced code blocks)?
**Answer:** The regex engine evaluates high-priority blocks (fenced code blocks) first and records their byte span indices. When scanning for Markdown table pipe patterns, any match whose start/end offsets overlap with an already shielded code block range is skipped, preventing code logic containing `|` operators from being misclassified as tables.

---

### Q24: What guarantees that placeholder tokens do not collide with actual user document text?
**Answer:** Each cleaning invocation generates a fresh 8-character hex string from `uuid.uuid4()`. The placeholder string follows the template `___SHIELDED_<uuid>_<idx>___`, rendering accidental collisions with document content statistically impossible.

---

### Q25: Why encapsulate provider tokenizers into a model-agnostic `BaseTokenizer` abstraction layer?
**Answer:** Decouples text chunking strategies from specific LLM vendors (e.g. OpenAI `tiktoken` vs Google Gemini `SentencePiece`). It enables dynamic injection of `GeminiEncoder`, `TiktokenEncoder`, or `HeuristicTokenizer`, preventing token estimation errors when deploying RAG systems across different LLM APIs.

---

### Q26: What parameter validation boundaries are enforced in `ChunkingStrategy.__init__` and why?
**Answer:** Enforces `chunk_size > 0`, `overlap >= 0`, `overlap < chunk_size`, and `min_chunk_size >= 0`. Preventing `overlap >= chunk_size` avoids infinite sliding window loops, while non-negative checks eliminate invalid negative array indexing.

---

### Q27: How does `_normalize_doc_args` support dual input types in `ChunkingStrategy.chunk()`?
**Answer:** Inspects the input payload: if a `LoadedDocument` instance is passed, it extracts `content` and `id`; if a raw string is passed, it uses `doc_id` or defaults to `"doc_0"`, ensuring polymorphic API flexibility across different callers.

---

### Q28: Why is using OpenAI's `tiktoken` as a universal tokenizer problematic when serving Google Gemini embeddings/LLMs?
**Answer:** OpenAI (`cl100k_base` / `o200k_base`) and Google Gemini use fundamentally different BPE and SentencePiece vocabulary encodings. For non-English texts (e.g. French), token counts between OpenAI and Gemini tokenizers can diverge by 10–25%. Using `tiktoken` for Gemini inputs can lead to context window overflow or unexpected chunk truncation.

