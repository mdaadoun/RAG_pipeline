# Session 8.1: Synthetic Test Corpus
**Date:** 2026-08-09

Implemented Synthetic Test Corpus management module in `src/ingestion/corpus.py` (`SyntheticCorpus`, `SyntheticFixtureSpec`) and registered default fixtures (`01_clean_doc.md`, `02_noisy_header.txt`, `03_table_split.md`, `04_corrupted_encoding.txt`). Provides self-healing fixture auto-generation, typed metadata listing, and integrity validation for benchmark test execution.

---

### 1. 🎓 Concepts Introduced
- **Synthetic Test Corpus:** A curated collection of benchmark documents engineered with deliberate quality variations, header noise, structural blocks, and corruption patterns to evaluate ingestion pipeline robustness.
- **Fixture Metadata Specification:** An immutable domain schema (`SyntheticFixtureSpec`) capturing fixture attributes, category classification, test intent, and expected pipeline outcomes.
- **Self-Healing Corpus:** A management mechanism in `SyntheticCorpus` that automatically verifies and recreates missing benchmark files on disk prior to execution.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Encapsulated Synthetic Corpus Domain Management]
- **Option 1:** Ad-hoc file path references in unit tests.
- **Option 2 (Selected):** Encapsulated `SyntheticCorpus` domain module in `src/ingestion/corpus.py`. Decouples tests and CLI tools from hardcoded paths, providing typed metadata, integrity checks, and self-healing fixture generation.

#### [ADR-02: Representative Four-Category Benchmark Suite]
- **Option 1:** Single generic markdown fixture.
- **Option 2 (Selected):** Four targeted failure mode fixtures (`01_clean_doc.md`, `02_noisy_header.txt`, `03_table_split.md`, `04_corrupted_encoding.txt`) targeting clean baselines, noisy headers, table/code orphan splits, and Unicode normalization.

#### [ADR-03: Self-Healing Fixture Auto-Generation]
- **Option 1:** Fail hard if fixture files are missing.
- **Option 2 (Selected):** Auto-generate missing default fixtures on demand via `ensure_default_fixtures()`. Guarantees test suite idempotency and seamless execution in clean CI/CD environments.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/corpus.py
class SyntheticFixtureSpec(BaseDomainModel):
    name: str
    category: str
    description: str
    expected_behavior: str
    file_path: Path | None = None

class SyntheticCorpus(BaseDomainModel):
    fixtures_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "tests" / "fixtures")

    def list_fixtures(self) -> list[SyntheticFixtureSpec]: ...
    def get_fixture_path(self, name: str) -> Path: ...
    def load_fixture_content(self, name: str) -> str: ...
    def ensure_default_fixtures(self) -> dict[str, Path]: ...
    def validate_corpus(self) -> dict[str, bool]: ...
```

```bash
# Run pytest verification suite
.venv/bin/pytest tests/unit/test_corpus.py tests/unit/test_structure.py -v
# Result: 138 passed in 0.32s
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Synthetic Corpus Module:** Created `src/ingestion/corpus.py` with `SyntheticCorpus`, `SyntheticFixtureSpec`, and `DEFAULT_FIXTURES`.
2. [x] **Benchmark Fixture Suite:** Scaffolded self-healing default benchmark fixtures under `tests/fixtures/`.
3. [x] **Package Export:** Exported corpus symbols in `src/ingestion/__init__.py`.
4. [x] **Unit Testing:** Implemented `tests/unit/test_corpus.py` and updated `tests/unit/test_structure.py`.
5. [x] **Quality Assurance:** Verified 100% compliance with `mypy --explicit-package-bases src`, `ruff check`, and full pytest suite.
