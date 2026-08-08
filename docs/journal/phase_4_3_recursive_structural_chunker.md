# Session 4.3: Recursive Structural Chunker
**Date:** 2026-08-08

Implemented `RecursiveStructuralChunker` with hierarchical delimiter splitting (`["\n# ", "\n## ", "\n### ", "\n\n", "\n", ". ", " "]`) and model-agnostic token boundary enforcement in `src/ingestion/chunkers.py`.

---

### 1. 🎓 Concepts Introduced
- **Recursive Structural Chunker:** Context-aware document segmentation strategy that recursively splits text across structural delimiters (headers, paragraphs, lines, sentences) while respecting model token bounds.
- **Hierarchical Separator Fallback:** An ordered sequence of structural delimiters evaluated sequentially to partition text into the largest valid sub-blocks fitting within max token constraints.
- **Leaf Span Partitioning:** Process of recursively partitioning text into contiguous atomic character ranges `[start_char, end_char]` prior to token-bounded candidate chunk merging.
- **Orphan Block Flag:** Boolean property (`is_orphan_block`) indicating whether a chunk boundary cuts through a protected structural element like a Markdown table or code block.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Hierarchical Separator Sequence Priority]
- **Option 1:** Splitting text by fixed character lengths regardless of formatting syntax.
- **Option 2 (Selected):** Configured ordered separator list `["\n# ", "\n## ", "\n### ", "\n\n", "\n", ". ", " "]` to split along structural boundaries first, preserving Markdown headings and paragraph semantics.

#### [ADR-02: Contiguous Leaf Span Character Offsets]
- **Option 1:** Reconstructing chunks via string concatenation and substring indexing search.
- **Option 2 (Selected):** Derived exact `(start, end)` integer character spans during recursive text partitioning, ensuring chunk contents match original slice indices `text[start_pos:end_pos]` with 100% character fidelity and zero string drift.

#### [ADR-03: Protected Block Orphan Shielding Integration]
- **Option 1:** Discarding table/code block protection check in recursive chunking.
- **Option 2 (Selected):** Integrated `TextCleaner.extract_protected_blocks(text)` to automatically flag partial table splits via `_create_chunk`, marking `is_orphan_block = True` for auditing.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/chunkers.py
class RecursiveStructuralChunker(ChunkingStrategy):
    """Context-aware recursive chunker respecting Markdown boundaries and token limits."""

    DEFAULT_SEPARATORS: ClassVar[list[str]] = [
        "\n# ",
        "\n## ",
        "\n### ",
        "\n\n",
        "\n",
        ". ",
        " ",
    ]

    def chunk(
        self, doc_or_text: Document | str, doc_id: str | None = None
    ) -> list[Chunk]:
        text, target_id = self._normalize_doc_args(doc_or_text, doc_id)
        if not text:
            return []

        protected = TextCleaner.extract_protected_blocks(text)
        leaf_spans = self._partition_text(text, 0, len(text), self.separators)
        # Merges leaf spans into target chunk_size and constructs Chunk objects
```

```bash
# Validation commands executed
.venv/bin/pytest
MYPYPATH=src .venv/bin/mypy --explicit-package-bases src/ingestion
.venv/bin/ruff check src/ tests/
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Recursive Structural Chunker:** Implemented `RecursiveStructuralChunker` in `src/ingestion/chunkers.py` with hierarchical delimiter fallback logic.
2. [x] **Model-Agnostic Tokenization:** Injected `BaseTokenizer` encoder interface for exact token limit verification (`count_tokens`).
3. [x] **Exact Character Range Offset Mapping:** Implemented `_partition_text` and `_fallback_spans` guaranteeing exact slice alignment `text[start:end]`.
4. [x] **Orphan Block Detection:** Connected `TextCleaner.extract_protected_blocks` to populate `is_orphan_block`.
5. [x] **Unit & Exports Test Suite:** Created unit tests (`test_recursive_structural_chunker_custom_separators`, `test_recursive_structural_chunker_empty_input`, `test_recursive_structural_chunker_markdown_hierarchy`) and registered package exports in `tests/unit/test_structure.py`. All 62 tests pass cleanly with zero type or lint errors.
