# Session 6.1: Pipeline Orchestrator Facade
**Date:** 2026-08-09

Implemented `PipelineOrchestrator` facade in `src/ingestion/pipeline.py` coordinating the full ingestion chain (Loaders → Cleaner → Chunkers → Monitor → Exporters) via typed `IngestionConfig`, producing both legacy `AuditReport` and per-document `IngestionReport` through an immutable `PipelineResult` container.

---

### 1. 🎓 Concepts Introduced
- **Facade Pattern:** Structural design pattern providing a simplified `run()` interface to the complex subsystem of loaders, cleaner, chunkers, monitor, and exporters.
- **PipelineOrchestrator:** Central facade class accepting a single typed `IngestionConfig` and coordinating all five pipeline stages behind one entry point.
- **PipelineResult:** Immutable frozen dataclass bundling `audit_report`, `ingestion_report`, `documents`, `chunks`, and `doc_reports` as a unified pipeline output.
- **Dual Report Model:** Simultaneous production of legacy `AuditReport` (aggregate metrics for CLI gating) and new `IngestionReport` (per-document `DocumentReport` list for diagnostics).

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Facade over Direct Stage Composition]
- **Option 1:** CLI directly wires loaders, cleaner, chunkers, and monitor inline.
- **Option 2 (Selected):** `PipelineOrchestrator` encapsulates all stage wiring behind `run()`, isolating callers from internal stage dependencies and enabling independent stage evolution.

#### [ADR-02: Typed IngestionConfig over Raw Primitives]
- **Option 1:** Pass `strategy_name`, `chunk_size`, `overlap` as constructor arguments (prior implementation).
- **Option 2 (Selected):** Accept a single `IngestionConfig` Pydantic model with enum-backed `strategy` and `tokenizer` fields, centralizing validation and enabling config serialization.

#### [ADR-03: Frozen Dataclass for PipelineResult]
- **Option 1:** Make `PipelineResult` a Pydantic `BaseDomainModel` for serialization consistency.
- **Option 2 (Selected):** Use frozen `@dataclass` to avoid circular imports (`pipeline.py` ↔ `models.py`) and keep the orchestration layer self-contained without Pydantic overhead.

#### [ADR-04: Backward-Compatible IngestionPipeline Wrapper]
- **Option 1:** Rename `IngestionPipeline` to `PipelineOrchestrator` and update all callers.
- **Option 2 (Selected):** Preserve `IngestionPipeline` as a thin wrapper delegating to `PipelineOrchestrator`, keeping CLI (`cli.py`) and integration tests unmodified.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/pipeline.py
@dataclass(frozen=True)
class PipelineResult:
    audit_report: AuditReport
    ingestion_report: IngestionReport
    documents: list[Document] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)
    doc_reports: list[DocumentReport] = field(default_factory=list)

class PipelineOrchestrator:
    def __init__(self, config: IngestionConfig | None = None) -> None:
        self._config = config or IngestionConfig()
        self._cleaner = TextCleaner()
        self._chunker = _build_chunker(self._config)
        self._monitor = IngestionMonitor(coverage_threshold=self._config.coverage_threshold)

    def run(self, input_dir, output_dir, report_path) -> PipelineResult:
        # Discover → process corpus → export JSONL + audit report → return result
        ...

    def _process_single_file(self, file_path: Path) -> tuple[Document | None, list[Chunk], DocumentReport]:
        # Load → clean → chunk → audit one file
        ...

class IngestionPipeline:
    # Backward-compat wrapper delegating to PipelineOrchestrator
    def run(self, input_dir, output_dir, report_path) -> AuditReport:
        return self._orchestrator.run(input_dir, output_dir, report_path).audit_report
```

```bash
# Verification suite execution
.venv/bin/pytest tests/unit/test_pipeline.py -v
.venv/bin/pytest tests/integration/test_pipeline.py -v
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **PipelineOrchestrator Facade:** Implemented full stage coordination (Loaders → Cleaner → Chunkers → Monitor → Exporters) via typed `IngestionConfig`.
2. [x] **PipelineResult Container:** Created immutable frozen dataclass bundling all pipeline outputs.
3. [x] **Dual Report Production:** Both `AuditReport` and `IngestionReport` generated per run.
4. [x] **Tokenizer Injection:** Config-driven tokenizer selection flows through `_build_chunker` factory into chunking strategies.
5. [x] **Backward Compatibility:** `IngestionPipeline` wrapper preserved for CLI and existing integration tests.
6. [x] **Unit Testing & Verification:** 15 unit tests in `tests/unit/test_pipeline.py` covering config/factory, file discovery, immutability, end-to-end runs, unsupported format shielding, empty corpus, error reports, and backward-compat wrapper. All 79 non-tiktoken-sandbox tests pass.
