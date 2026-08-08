# Session 4.2: Fixed-Size Token Chunker
**Date:** 2026-08-08

Implemented `FixedSizeChunker` utilizing exact token-based sliding windows based on `chunk_size` and `overlap` tokens from the injected `BaseTokenizer` instance in `src/ingestion/chunkers.py`.

---

### 1. 🎓 Concepts Introduced
- **Fixed-Size Token Chunker:** Document chunking strategy that partitions text strictly according to exact token count windows (`chunk_size`) and token overlaps (`overlap`).
- **Dual-Mode Token Sliding Window:** Algorithm selecting exact token ID slicing for loss-less tokenizers (`TiktokenEncoder`) vs binary-search token windowing for heuristic/stub tokenizers (`GeminiEncoder`, `HeuristicTokenizer`).
- **Character Offset Mapping from Token Slices:** Reconstructing exact document `start_char` and `end_char` offsets by decoding token prefixes to ensure 100% text-to-chunk alignment.
- **Orphan Block Detection Boundary Logic:** Evaluating protected Markdown element bounds (tables, code blocks) against chunk character ranges to flag partial splits (`is_orphan_block = True`).

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Dual-Mode Sliding Window Execution]
- **Option 1:** Forcing character sliding window approximation across all tokenizers.
- **Option 2 (Selected):** Implemented dual-mode execution: token ID slicing for tokenizers with loss-less `decode()` roundtrips (`TiktokenEncoder`) and binary-search token counting windowing over character slices for non-lossless tokenizers (`GeminiEncoder`, `HeuristicTokenizer`). Guarantees exact token limits across any provider.

#### [ADR-02: Exact Token Prefix Offset Decoding]
- **Option 1:** Estimating character start positions using average character-per-token ratios.
- **Option 2 (Selected):** Calculated `start_char = len(self.decode(tokens[:start_tok]))` and `end_char = start_char + len(chunk_text)`. Guarantees exact character slicing matching `text[start_char:end_char] == chunk_text`.

#### [ADR-03: Orphan Block Detection Boundary Logic]
- **Option 1:** Ignoring table splits in `FixedSizeChunker`.
- **Option 2 (Selected):** Checked `p_start < end_char and start_char < p_end and not (start_char <= p_start and end_char >= p_end)` for all protected blocks, flagging chunks that sever tables or code blocks mid-structure.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/chunkers.py
class FixedSizeChunker(ChunkingStrategy):
    """Rigid fixed-length token sliding window chunker with fixed overlap."""

    def chunk(
        self, doc_or_text: Document | str, doc_id: str | None = None
    ) -> list[Chunk]:
        text, target_id = self._normalize_doc_args(doc_or_text, doc_id)
        if not text:
            return []

        chunks: list[Chunk] = []
        idx = 0
        protected_blocks = TextCleaner.extract_protected_blocks(text)
        step_tokens = max(1, self.chunk_size - self.overlap)
        tokens = self.encode(text)
        # Slices tokens by step_tokens and computes exact token counts and orphan flags
```

```bash
# Validation commands executed
.venv/bin/pytest
.venv/bin/mypy --explicit-package-bases src config tests
.venv/bin/ruff check src tests config
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Fixed-Size Token Chunker:** Implemented exact token sliding window algorithm in `FixedSizeChunker` within `src/ingestion/chunkers.py`.
2. [x] **Dual-Mode Engine:** Added token-ID slicing for `TiktokenEncoder` and binary-search windowing for `GeminiEncoder`/`HeuristicTokenizer`.
3. [x] **Orphan Block Flagging:** Integrated structural protection shielding checks to set `is_orphan_block` on table splits.
4. [x] **Unit Test Suite:** Added unit tests `test_fixed_size_token_chunker_exact_counts`, `test_fixed_size_token_chunker_empty_input`, and `test_fixed_size_token_chunker_orphan_detection` in `tests/unit/test_chunkers.py`. All 59 tests pass with zero type errors.
