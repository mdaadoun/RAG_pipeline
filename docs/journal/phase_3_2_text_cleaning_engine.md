# Session 3.2: Text Cleaning Engine & Structural Protection Shielding
**Date:** 2026-08-08

Designed and implemented the text cleaning and normalization engine in `src/ingestion/cleaner.py` centered on `TextCleaner`. Integrated Unicode NFKC normalization, control character stripping, whitespace capping ($\le 2$ consecutive `\n`), repetitive header/footer line deduplication ($N=3$), and placeholder-based structural protection shielding for Markdown tables and fenced code blocks. Trapped all cleaning errors into domain `CleanError` exceptions and expanded the unit test suite in `tests/unit/test_cleaner.py`.

---

### 1. 🎓 Concepts Introduced
- **NFKC Unicode Normalization:** Applying standard Unicode Normalization Form KC (Compatibility Decomposition followed by Canonical Composition) to standardize compatibility characters, ligatures, and non-breaking spaces into uniform tokens.
- **Structural Protection Shielding:** Masking syntax-sensitive blocks (fenced code blocks and Markdown tables) with unique UUID-prefixed placeholder tokens (`___SHIELDED_<uuid>_<idx>___`) prior to cleaning operations to prevent structural corruption.
- **Boilerplate Line Deduplication:** Frequency-based filtering algorithm that removes non-empty header/footer lines repeating across more than $N$ occurrences throughout document content while bypassing shielded placeholders.
- **CleanError Exception Shielding:** Trapping input validation failures and runtime string manipulation errors within `CleanError` domain exceptions to maintain zero-naked-crash pipeline guarantees.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Placeholder-Based Structural Shielding]
- **Option 1:** Cleaning all text naively with line-by-line regexes without separating code blocks or tables.
- **Option 2 (Selected):** Substituted fenced code blocks (``` / ~~~) and Markdown tables (|...|) with unique UUID-prefixed tokens (`___SHIELDED_<uuid>_<idx>___`), applying text transformations on unshielded regions only before unshielding verbatim. Prevents whitespace capping from destroying table alignments or code block indentations.

#### [ADR-02: NFKC Unicode Normalization & Control Char Stripping]
- **Option 1:** Performing basic string `.strip()` and manual replacement of specific control characters.
- **Option 2 (Selected):** Integrated `unicodedata.normalize("NFKC", text)` with regex filtering of non-printable ASCII control characters (`\x00-\x08\x0b\x0c\x0e-\x1f`). Ensures visual equivalences are standardized for downstream tokenizers.

#### [ADR-03: Line-Based Boilerplate Deduplication]
- **Option 1:** Manually writing hardcoded header/footer blacklist regex rules.
- **Option 2 (Selected):** Implemented dynamic line occurrence counting across unshielded text. Any non-empty line repeating $> \text{threshold}$ times (default $N=3$) is automatically pruned.

#### [ADR-04: Domain Exception Shielding via CleanError]
- **Option 1:** Letting raw `TypeError` or regex execution failures bubble up unhandled.
- **Option 2 (Selected):** Input type validation and try-except blocks catch failures and re-raise `CleanError` populated with structured context metadata.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/cleaner.py
import re
import unicodedata
import uuid

from ingestion.exceptions import CleanError


class TextCleaner:
    """Document text cleaning, normalization, and protection engine."""

    def __init__(
        self,
        normalize_unicode: bool = True,
        remove_control_chars: bool = True,
        cap_newlines: bool = True,
        max_newlines: int = 2,
        boilerplate_threshold: int | None = 3,
        shield_protected: bool = True,
    ) -> None:
        self.normalize_unicode = normalize_unicode
        self.remove_control_chars = remove_control_chars
        self.cap_newlines = cap_newlines
        self.max_newlines = max_newlines
        self.boilerplate_threshold = boilerplate_threshold
        self.shield_protected = shield_protected

    def clean(self, text: str, boilerplate_threshold: int | None = None) -> str:
        """Clean and normalize raw document text while preserving protected blocks."""
        if not isinstance(text, str):
            raise CleanError("Input text must be a string", details={"provided_type": str(type(text))})
        ...
```

```bash
# Validation commands executed
.venv/bin/pytest tests/unit/test_cleaner.py
.venv/bin/mypy src/
.venv/bin/ruff check src/ tests/
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Text Cleaning Engine:** Implemented `TextCleaner` in `src/ingestion/cleaner.py` supporting NFKC normalization and control character stripping.
2. [x] **Whitespace & Newline Capping:** Standardized spaces and capped consecutive newlines to maximum of 2 (`\n\n`).
3. [x] **Boilerplate Line Deduplication:** Added line frequency tracking to prune lines exceeding `boilerplate_threshold`.
4. [x] **Structural Protection Shielding:** Implemented `extract_protected_blocks`, `_shield_protected_blocks`, and `_unshield_protected_blocks` to preserve code fences and Markdown tables.
5. [x] **Package Exports & Pipeline Integration:** Exported `TextCleaner` in `src/ingestion/__init__.py`.
6. [x] **Unit Testing Suite:** Expanded `tests/unit/test_cleaner.py` and `tests/unit/test_structure.py` to 44 passing unit tests with 100% Mypy strict coverage.
