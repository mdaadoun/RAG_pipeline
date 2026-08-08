# Session 3.3: Structural Protection Shielding
**Date:** 2026-08-08

Implemented regular expression shielding in `TextCleaner` (`src/ingestion/cleaner.py`) to isolate Markdown tables (`^\|.*\|$`) and fenced code blocks (``` and ~~~) using UUID-prefixed placeholders during text normalization, whitespace capping, and boilerplate deduplication.

---

### 1. 🎓 Concepts Introduced
- **Structural Protection Shielding:** A cleaning pipeline technique that masks structured blocks (Markdown tables, code blocks) with placeholder tokens during normalization to prevent structural corruption.
- **UUID-Prefixed Placeholder Token:** A unique token format (`___SHIELDED_<uuid>_<idx>___`) inserted in place of protected text regions to guarantee zero collision with document contents.
- **Table Pipe Regex Shielding:** Regular expression matching pattern (`^\|.*\|$) that detects contiguous rows of Markdown pipe-delimited tabular data.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: UUID-Prefixed Token Substitution]
- **Option 1:** Cleaning all text naively with line-by-line regexes without separating code blocks or tables.
- **Option 2 (Selected):** Substituted fenced code blocks (``` / ~~~) and Markdown tables (|...|) with unique UUID-prefixed tokens (`___SHIELDED_<uuid>_<idx>___`), applying text transformations on unshielded regions only before unshielding verbatim. Prevents whitespace capping from destroying table alignments or code block indentations.

#### [ADR-02: Multi-Pattern Regex Detection for Tables and Fenced Code]
- **Option 1:** Parsing Markdown with a full AST parser (e.g. mistune/markdown-it) which introduces heavy external dependencies and execution overhead.
- **Option 2 (Selected):** Multi-pattern regex detection with overlap prevention. Evaluates high-priority code block matches first, then detects table pipe boundaries while skipping spans that fall within code block offsets.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/cleaner.py
@staticmethod
def extract_protected_blocks(text: str) -> list[tuple[int, int, str]]:
    """Identify line boundaries of Markdown tables and code blocks."""
    protected: list[tuple[int, int, str]] = []
    # Code blocks fenced by ``` or ~~~
    for match in re.finditer(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)", text):
        protected.append((match.start(), match.end(), "code_block"))

    # Markdown tables matching lines starting with | and ending with | (^\|.*\|$)
    table_pattern = r"(?:^|\n)([ \t]*\|.*\|[ \t]*(?:\n[ \t]*\|.*\|[ \t]*)*)"
    for match in re.finditer(table_pattern, text):
        start = match.start(1)
        end = match.end(1)
        if not any(
            (p_start <= start < p_end) or (p_start < end <= p_end) or (start <= p_start and end >= p_end)
            for p_start, p_end, _ in protected
        ):
            protected.append((start, end, "table"))

    protected.sort(key=lambda item: item[0])
    return protected
```

```bash
# Validation commands executed
.venv/bin/pytest
.venv/bin/mypy --explicit-package-bases src tests
.venv/bin/ruff check src tests config
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Markdown Table Pipe Shielding:** Extended `extract_protected_blocks` regex to detect contiguous table rows starting and ending with `|`.
2. [x] **Fenced Code Block Shielding:** Verified `~~~` and ```` ``` ```` fenced block extraction and placeholder masking.
3. [x] **Overlap Prevention Engine:** Ensured pipe characters inside code blocks are not misclassified as tables.
4. [x] **Loader & Cleaner Integration:** Expanded unit test suite in `tests/unit/test_cleaner.py` and `tests/unit/test_loaders.py` to 47 passing tests with 100% typing and linting compliance.
