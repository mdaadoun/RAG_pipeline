# Session 5.2: Orphan Block Detector
**Date:** 2026-08-08

Implemented `OrphanBlockDetector` in `src/ingestion/detector.py` to identify Markdown tables, fenced code blocks, and block math severed across chunk boundaries, ensuring structural integrity during RAG ingestion.

---

### 1. 🎓 Concepts Introduced
- **Orphan Block:** A Markdown structural entity (table, code block, math block) split across chunk boundaries such that no single chunk contains the complete block.
- **Structural Block Range:** The exact character start and end index span (`[start_char, end_char]`) of a contiguous structural element within cleaned text.
- **Block Preservation:** The condition where at least one generated chunk entirely spans a structural block range without boundary truncation.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Decoupled Orphan Detector Module]
- **Option 1:** Keeping orphan detection inline within `IngestionMonitor`.
- **Option 2 (Selected):** Extracting `OrphanBlockDetector` and `StructuralBlock` into `src/ingestion/detector.py`, conforming to 250 LOC modular design bounds and single-responsibility principles.

#### [ADR-02: Range Intersection Preservation Logic]
- **Option 1:** Checking simple chunk boundary character equality.
- **Option 2 (Selected):** Evaluating all chunks intersecting a structural block range and verifying if any single chunk satisfies `c.start_char <= block.start_char and c.end_char >= block.end_char`.

#### [ADR-03: Multiline Regex Structural Scanner vs AST]
- **Option 1:** Integrating a full Markdown AST parser dependency.
- **Option 2 (Selected):** Implementing compiled multiline regex patterns for Markdown pipe tables (`(?:^|\n)(\|[^\n]+\|\n?)+`), code fences (``` / ~~~), and math blocks (`$$`), offering zero external dependency weight and microsecond execution speed.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/detector.py
class StructuralBlock(NamedTuple):
    """Immutable representation of a document structural block range."""
    block_type: str
    start_char: int
    end_char: int
    content: str

class OrphanBlockDetector:
    """Scanner for detecting Markdown tables and code blocks split across chunk boundaries."""

    def extract_structural_blocks(self, text: str) -> list[StructuralBlock]:
        # Returns list of StructuralBlock instances with start and end character spans
        ...

    def detect_orphan_blocks(self, cleaned_text: str, chunks: list[Chunk]) -> int:
        # Returns total count of structural blocks severed across chunk boundaries
        ...
```

```bash
# Validation commands executed
.venv/bin/pytest
.venv/bin/mypy --explicit-package-bases src/
.venv/bin/ruff check src tests
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Decoupled Module Creation:** Implemented `OrphanBlockDetector` in `src/ingestion/detector.py`.
2. [x] **Regex Block Extraction:** Implemented regex pattern matching for Markdown pipe tables, fenced code blocks, and block math.
3. [x] **Single-Chunk Preservation Evaluation:** Built character range intersection logic to detect severed structural boundaries.
4. [x] **IngestionMonitor Integration:** Delegated orphan block scanning in `IngestionMonitor` to `OrphanBlockDetector`.
5. [x] **Unit Test Suite Expansion:** Created `tests/unit/test_detector.py` and updated `tests/unit/test_structure.py`. All 73 pytest unit tests pass cleanly with zero MyPy or Ruff errors.
