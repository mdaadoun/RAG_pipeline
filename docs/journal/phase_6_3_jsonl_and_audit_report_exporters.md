# Session 6.3: JSONL & Audit Report Exporters
**Date:** 2026-08-09

Implemented modular JSONL and Audit Report Exporters (`BaseExporter` ABC, `JSONLChunkExporter`, `AuditReportExporter`) with streaming and round-trip deserialization capabilities, integrated them into `PipelineOrchestrator`, and refactored `json_utils.py` for DRY backward compatibility.

---

### 1. 🎓 Concepts Introduced
- **JSONL (JSON Lines):** A streamable text format where each line is a valid JSON object, optimized for line-by-line parsing, vector database ingestion, and large dataset chunking.
- **JSONLChunkExporter:** Exporter module responsible for serializing `Chunk` domain models into UTF-8 encoded JSON Lines files with automatic parent directory creation.
- **AuditReportExporter:** Exporter module responsible for formatting and serializing `AuditReport` and `IngestionReport` domain models into indented JSON files.
- **Round-trip Deserialization:** The process of reading exported JSON/JSONL artifacts back into strongly typed Pydantic domain models to verify serialization losslessness and schema adherence.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: BaseExporter Generic ABC Contract]
- **Option 1:** Write ad-hoc procedural functions directly inside `json_utils.py` or inline in `pipeline.py`.
- **Option 2 (Selected):** Define a generic `BaseExporter[T]` abstract base class establishing a uniform `export(data: T, output_path: str | Path) -> Path` contract. Decouples output formatting concerns from pipeline orchestration and enables clean extension for future exporters (e.g. Parquet or Vector DB).

#### [ADR-02: Streaming and Batch JSONL Export]
- **Option 1:** Support only full-list in-memory batch serialization.
- **Option 2 (Selected):** Provide `export_stream(chunks: Iterable[Chunk], ...)` accepting any iterable/generator for memory-efficient line-by-line streaming, alongside batch `export()`, minimizing memory overhead when processing large document corpora.

#### [ADR-03: Bi-directional Serialization & Round-trip Validation]
- **Option 1:** Provide write-only export functions.
- **Option 2 (Selected):** Incorporate `read()`, `read_audit_report()`, and `read_ingestion_report()` methods backed by Pydantic V2 `model_validate_json()`. Guarantees round-trip data integrity verification and simplifies integration testing.

#### [ADR-04: Delegated json_utils for Backward Compatibility]
- **Option 1:** Delete `json_utils.py` and require all callers to rewrite imports to `ingestion.exporters`.
- **Option 2 (Selected):** Refactor legacy `save_chunks_jsonl()` and `save_audit_report()` in `json_utils.py` to delegate directly to procedural exporter functions (`export_chunks_jsonl`, `export_audit_report`). Preserves DRY principles and backward compatibility for existing callers.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/exporters.py
class BaseExporter(ABC, Generic[T]):
    @abstractmethod
    def export(self, data: T, output_path: str | Path) -> Path:
        ...

class JSONLChunkExporter(BaseExporter[list[Chunk]]):
    def export_stream(self, chunks: Iterable[Chunk], output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(chunk.model_dump_json(by_alias=True) + "\n")
        return path

    def read(self, input_path: str | Path) -> list[Chunk]:
        ...

class AuditReportExporter(BaseExporter[BaseDomainModel]):
    def export(self, data: BaseDomainModel, output_path: str | Path, indent: int = 2) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        json_str = data.model_dump_json(indent=indent)
        path.write_text(json_str, encoding="utf-8")
        return path
```

```bash
# Verification suite execution
.venv/bin/pytest tests/unit/test_exporters.py tests/integration/test_pipeline.py -v
# Result: 113 passed in 0.25s
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **BaseExporter Generic ABC:** Defined abstract generic base class for exporter implementations.
2. [x] **JSONLChunkExporter Class:** Implemented JSONL chunk serialization with `export()`, `export_stream()`, and `read()`.
3. [x] **AuditReportExporter Class:** Implemented formatted JSON report serialization with `export()`, `read_audit_report()`, and `read_ingestion_report()`.
4. [x] **Procedural Export Helpers:** Added `export_chunks_jsonl` and `export_audit_report` for convenient one-line invocations.
5. [x] **json_utils Delegation:** Updated `json_utils.py` functions to delegate to exporter helpers maintaining DRY backward compatibility.
6. [x] **Orchestrator Integration:** Integrated exporters into `PipelineOrchestrator.run()` for automatic `chunks.jsonl` and `rapport_ingestion.json` creation.
7. [x] **Unit & Integration Tests:** Created 7 unit tests in `tests/unit/test_exporters.py` and updated `tests/integration/test_pipeline.py`. All 113 tests pass cleanly.
