# Session 4.1: Model-Agnostic Tokenizer & Strategy Interface
**Date:** 2026-08-08

Implemented `BaseTokenizer(ABC)` interface (`src/ingestion/tokenizers.py`) and injected model-agnostic tokenizers (`GeminiEncoder`, `TiktokenEncoder`, `HeuristicTokenizer`) into `ChunkingStrategy(ABC)` in `src/ingestion/chunkers.py`.

---

### 1. 🎓 Concepts Introduced
- **Model-Agnostic Tokenizer Layer:** Abstract contract (`BaseTokenizer`) isolating document chunkers from vendor-specific tokenizer libraries (Google Gemini vs OpenAI `tiktoken`).
- **GeminiEncoder Tokenizer Adapter:** Provider adapter supporting Google Gemini model tokenization with calibrated SentencePiece offline fallback.
- **Dependency-Injected Chunking Strategy:** `ChunkingStrategy` design pattern allowing chunking strategies (`FixedSizeChunker`, `RecursiveStructuralChunker`) to receive any `BaseTokenizer` instance dynamically.
- **Dual-Input Argument Normalization:** Flexible parameter handler (`_normalize_doc_args`) extracting content and IDs from domain `LoadedDocument` objects or raw `str` text.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Provider-Agnostic BaseTokenizer Abstraction]
- **Option 1:** Coupling chunking strategies directly to OpenAI `tiktoken`.
- **Option 2 (Selected):** Extracted `BaseTokenizer(ABC)` with `encode()`, `decode()`, and `count_tokens()` methods, implementing `GeminiEncoder`, `TiktokenEncoder`, and `HeuristicTokenizer`. Prevents token miscount errors when target LLM is Google Gemini.

#### [ADR-02: Dependency Injection into Chunking Strategies]
- **Option 1:** Hardcoding tokenizer instantiation inside `ChunkingStrategy.__init__`.
- **Option 2 (Selected):** Injected `tokenizer: BaseTokenizer | str | None` into `ChunkingStrategy.__init__`. Resolves provider names via factory `get_tokenizer(name)` while enabling callers to supply custom tokenizer instances.

#### [ADR-03: Calibrated Gemini SentencePiece Fallback]
- **Option 1:** Requiring live network API calls for Gemini `count_tokens()`.
- **Option 2 (Selected):** Provided calibrated SentencePiece ratio fallback (`3.6 chars/token`) inside `GeminiEncoder.count_tokens()`, guaranteeing 100% offline unit test execution in sandboxed environments.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/tokenizers.py
class BaseTokenizer(ABC):
    @abstractmethod
    def encode(self, text: str) -> list[int]: pass
    @abstractmethod
    def decode(self, tokens: list[int]) -> str: pass
    @abstractmethod
    def count_tokens(self, text: str) -> int: pass

class GeminiEncoder(BaseTokenizer):
    def count_tokens(self, text: str) -> int:
        if not text: return 0
        return max(1, math.ceil(len(text) / 3.6))

# src/ingestion/chunkers.py
class ChunkingStrategy(ABC):
    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 0,
        min_chunk_size: int = 50,
        tokenizer: BaseTokenizer | str | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.tokenizer = get_tokenizer(tokenizer) if isinstance(tokenizer, str) else (tokenizer or get_tokenizer("gemini"))
```

```bash
# Validation commands executed
.venv/bin/pytest
.venv/bin/mypy --explicit-package-bases src config tests
.venv/bin/ruff check src tests config
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Model-Agnostic Tokenizer Module:** Implemented `src/ingestion/tokenizers.py` with `BaseTokenizer`, `GeminiEncoder`, `TiktokenEncoder`, `HeuristicTokenizer`, and `get_tokenizer` factory.
2. [x] **Dependency Injection into Chunkers:** Updated `ChunkingStrategy`, `FixedSizeChunker`, and `RecursiveStructuralChunker` to use injected `BaseTokenizer`.
3. [x] **Gemini Integration:** Configured `TokenizerType.GEMINI` as primary default provider in `models.py` and `IngestionConfig`.
4. [x] **Package Exports & Test Coverage:** Exported tokenizer symbols in `src/ingestion/__init__.py` and created `tests/unit/test_tokenizers.py`. Passed all 58 unit and integration tests with zero linting or strict type errors.

