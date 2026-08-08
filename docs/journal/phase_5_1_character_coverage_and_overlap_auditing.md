# Session 5.1: Character Coverage & Overlap Auditing
**Date:** 2026-08-08

Implemented `IngestionMonitor` in `src/ingestion/monitor.py` to evaluate document retention, calculate character coverage and overlap duplicate ratios, scan for orphan Markdown tables/code blocks, and produce structured audit reports.

---

### 1. 🎓 Concepts Introduced
- **Character Coverage Ratio (`char_coverage_ratio`):** The proportion of unique source text characters present in at least one generated chunk relative to total cleaned character count ($\ge 0.98$ target).
- **Duplicate Character Ratio (`duplicate_char_ratio`):** Ratio of extra character reads across chunks resulting from configured chunk overlap or redundant text slicing.
- **Orphan Block Scanner:** Regex-based detector identifying Markdown table rows or fenced code block boundaries split across separate chunks.
- **Document & Ingestion Reports:** Structured Pydantic V2 domain models (`DocumentReport` and `IngestionReport`) recording per-document and corpus-level quality metrics.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Set-Based Character Index Tracking]
- **Option 1:** Calculating coverage using simple string lengths of output chunks vs original doc length.
- **Option 2 (Selected):** Aggregating unique character indices `set(range(start_char, end_char))` per document, accurately measuring unique retention without double-counting overlapping regions.

#### [ADR-02: Regex-Based Structural Orphan Block Scanner]
- **Option 1:** Relying solely on `is_orphan_block` chunk flags set by chunking strategies.
- **Option 2 (Selected):** Combining chunk flags with regular expression scanners in `_detect_orphan_blocks` for Markdown tables (`^\|.*\|$`) and fenced code blocks (``` / ~~~), ensuring structural boundary splits are flagged as blocking error alerts.

#### [ADR-03: Dual-Level Audit Reporting Facade]
- **Option 1:** Generating only a global aggregate audit metrics summary.
- **Option 2 (Selected):** Implementing `audit_document` for granular per-file reports (`DocumentReport`), `audit` for legacy `AuditReport` compatibility, and `create_ingestion_report` for full pipeline deliverable reports (`IngestionReport`).

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/monitor.py
class IngestionMonitor:
    """Quality assurance and information loss audit engine."""

    def __init__(
        self,
        min_chunk_size: int = 20,
        max_overlap_tolerance: float = 0.05,
        coverage_threshold: float = 0.98,
    ) -> None:
        self.min_chunk_size = min_chunk_size
        self.max_overlap_tolerance = max_overlap_tolerance
        self.coverage_threshold = coverage_threshold

    def audit_document(
        self, document_id: str, source_path: str, cleaned_text: str, chunks: list[Chunk], ...
    ) -> DocumentReport:
        # Calculates set-based char_coverage_ratio, duplicate_char_ratio, and orphan_blocks
```

```bash
# Validation commands executed
.venv/bin/pytest
.venv/bin/mypy --explicit-package-bases src/
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Character Coverage Calculation:** Implemented exact unique character index set tracking for `char_coverage_ratio`.
2. [x] **Duplicate Character Ratio:** Calculated overlap duplicate ratio `duplicate_char_ratio` relative to cleaned source character length.
3. [x] **Orphan Block Detector:** Built `_detect_orphan_blocks` scanner detecting split Markdown tables and fenced code blocks.
4. [x] **Document & Ingestion Reports:** Implemented `audit_document`, `audit`, and `create_ingestion_report` generating typed `DocumentReport`, `AuditReport`, and `IngestionReport` outputs.
5. [x] **Unit Test Suite Expansion:** Created unit tests in `tests/unit/test_monitor.py` covering pass status, low coverage warnings, orphan detection, duplicate ratios, and report aggregation. All 67 pytest cases pass cleanly with zero MyPy errors.
