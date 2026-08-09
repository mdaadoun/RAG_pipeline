# Session 6.2: File-Level Exception Shielding
**Date:** 2026-08-09

Implemented per-stage exception shielding in `src/ingestion/file_shield.py` and refactored `PipelineOrchestrator._process_single_file` to wrap each sub-stage (load, read, clean, chunk, audit) independently, capturing full Python tracebacks into `DocumentReport.errors` without crashing directory batch runs.

---

### 1. 🎓 Concepts Introduced
- **Exception Shielding:** Design pattern wrapping each sub-operation in its own `try/except` to prevent one failure from cascading through the entire batch pipeline.
- **FileShieldContext:** Per-file mutable accumulator collecting `StageError` objects from each processing stage, providing formatted error messages and full traceback retrieval.
- **StageError:** Frozen dataclass capturing a single stage failure with stage name, exception type, message string, and full `traceback.format_exception()` output.
- **IngestionStage:** Enum (`LOAD`, `CLEAN`, `CHUNK`, `AUDIT`) tagging errors to their pipeline origin for granular failure attribution.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Accumulator Pattern over Inline Try/Except]
- **Option 1:** Catch exceptions directly inside `_process_single_file` with multiple inline `try/except` blocks.
- **Option 2 (Selected):** Introduce `FileShieldContext` as a dedicated accumulator separating error collection from control flow, enabling multi-error accumulation, independent testability, and keeping `_process_single_file` readable as a linear stage sequence.

#### [ADR-02: Broad Exception Boundary over IngestionError-Only]
- **Option 1:** Catch only `IngestionError` subclasses at each stage boundary (previous approach).
- **Option 2 (Selected):** Catch `Exception` at each shield boundary to guard against unexpected third-party exceptions (Pydantic validation, OS-level I/O, tokenizer errors). Full traceback capture provides diagnostic context regardless of exception hierarchy.

#### [ADR-03: Dedicated Shield Methods over Monolithic Handler]
- **Option 1:** Single `try/except` around the entire load → clean → chunk → audit chain.
- **Option 2 (Selected):** Five dedicated `_shield_*` methods (`_shield_load`, `_shield_read`, `_shield_clean`, `_shield_chunk`, `_shield_audit`) each wrapping one sub-stage. Adds ~80 LOC but enables pinpoint error attribution, per-stage testability, and future partial-success extensibility.

#### [ADR-04: Traceback Capture via format_exception]
- **Option 1:** Store only `str(exc)` in error messages (compact but loses stack trace).
- **Option 2 (Selected):** Capture full Python tracebacks via `traceback.format_exception()` into `StageError.traceback` for post-mortem debugging, while `format_short()` provides compact `[stage] ErrorType: message` summaries for `DocumentReport.errors`.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/file_shield.py
class IngestionStage(str, Enum):
    LOAD = "load"
    CLEAN = "clean"
    CHUNK = "chunk"
    AUDIT = "audit"

@dataclass(frozen=True)
class StageError:
    stage: IngestionStage
    error_type: str
    message: str
    traceback: str

@dataclass
class FileShieldContext:
    file_path: Path
    errors: list[StageError] = field(default_factory=list)

    def record_error(self, stage: IngestionStage, exc: BaseException) -> None:
        # Captures full traceback + logs structured warning
        ...

    def format_error_messages(self) -> list[str]:
        # Returns ["[stage] ErrorType: message", ...] for DocumentReport.errors
        ...
```

```python
# src/ingestion/pipeline.py — refactored _process_single_file
def _process_single_file(self, file_path: Path) -> tuple[Document | None, list[Chunk], DocumentReport]:
    ctx = FileShieldContext(file_path=file_path)
    loader = self._shield_load(file_path, ctx)       # Stage: LOAD
    raw_doc = self._shield_read(loader, ...)          # Stage: LOAD (read)
    cleaned = self._shield_clean(raw_doc.content, ...)  # Stage: CLEAN
    file_chunks = self._shield_chunk(doc, ...)        # Stage: CHUNK
    report = self._shield_audit(doc, file_chunks, ctx)  # Stage: AUDIT
    return doc, file_chunks, report
```

```bash
# Verification suite execution
.venv/bin/pytest tests/unit/test_file_shield.py tests/unit/test_pipeline.py -v
# Result: 29 passed, 0 failed
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **FileShieldContext Accumulator:** Implemented per-file error accumulator with `record_error()`, `format_error_messages()`, and `format_tracebacks()`.
2. [x] **IngestionStage Enum:** Defined LOAD, CLEAN, CHUNK, AUDIT stages for error attribution tagging.
3. [x] **StageError Dataclass:** Frozen dataclass capturing stage, exception type, message, and full traceback string.
4. [x] **Per-Stage Shield Methods:** Refactored `_process_single_file` into `_shield_load`, `_shield_read`, `_shield_clean`, `_shield_chunk`, `_shield_audit`.
5. [x] **Traceback Preservation:** Full Python tracebacks captured via `traceback.format_exception()` without crashing batch runs.
6. [x] **Unit Testing & Verification:** 14 new tests in `tests/unit/test_file_shield.py` covering StageError immutability, FileShieldContext accumulation, all shield methods, batch continuation, and traceback preservation. All 29 targeted tests pass with zero regressions.
