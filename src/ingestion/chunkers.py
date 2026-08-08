"""Chunking strategies using dependency-injected model-agnostic tokenizers."""

from abc import ABC, abstractmethod
from typing import ClassVar

from ingestion.cleaner import TextCleaner
from ingestion.exceptions import ChunkError
from ingestion.models import Chunk, Document
from ingestion.tokenizers import BaseTokenizer, get_tokenizer


class ChunkingStrategy(ABC):
    """Abstract Base Class for document chunking strategies using model-agnostic tokenization."""

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 0,
        min_chunk_size: int = 50,
        tokenizer: BaseTokenizer | str | None = None,
    ) -> None:
        """Initialize chunker strategy parameters and token encoder."""
        if chunk_size <= 0:
            raise ChunkError("chunk_size must be positive")
        if overlap < 0:
            raise ChunkError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ChunkError("overlap must be strictly smaller than chunk_size")
        if min_chunk_size < 0:
            raise ChunkError("min_chunk_size must be non-negative")

        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

        if tokenizer is None:
            self.tokenizer = get_tokenizer("tiktoken")
        elif isinstance(tokenizer, str):
            self.tokenizer = get_tokenizer(tokenizer)
        else:
            self.tokenizer = tokenizer

    def count_tokens(self, text: str) -> int:
        """Count tokens using underlying injected tokenizer."""
        return self.tokenizer.count_tokens(text)

    def encode(self, text: str) -> list[int]:
        """Encode text to token list using underlying injected tokenizer."""
        return self.tokenizer.encode(text)

    def decode(self, tokens: list[int]) -> str:
        """Decode token list to text using underlying injected tokenizer."""
        return self.tokenizer.decode(tokens)

    def _normalize_doc_args(
        self, doc_or_text: Document | str, doc_id: str | None = None
    ) -> tuple[str, str]:
        """Helper to extract text and doc_id from Document or raw text string."""
        if isinstance(doc_or_text, Document):
            return doc_or_text.content, doc_or_text.id
        target_id = doc_id if doc_id is not None else "doc_0"
        return doc_or_text, target_id

    def _create_chunk(
        self,
        doc_id: str,
        index: int,
        content: str,
        start_char: int,
        end_char: int,
        token_count: int,
        protected_blocks: list[tuple[int, int, str]],
    ) -> Chunk:
        """Construct typed Chunk object with calculated orphan block flag."""
        is_orphan = any(
            p_start < end_char
            and start_char < p_end
            and not (start_char <= p_start and end_char >= p_end)
            for p_start, p_end, _ in protected_blocks
        )
        return Chunk(
            id=f"{doc_id}_chk_{index}",
            doc_id=doc_id,
            chunk_index=index,
            content=content,
            start_char=start_char,
            end_char=end_char,
            token_count=token_count,
            is_orphan_block=is_orphan,
        )

    @abstractmethod
    def chunk(
        self, doc_or_text: Document | str, doc_id: str | None = None
    ) -> list[Chunk]:
        """Split document or text into typed Chunk objects."""
        pass


BaseChunker = ChunkingStrategy


class FixedSizeChunker(ChunkingStrategy):
    """Rigid fixed-length token sliding window chunker with fixed overlap."""

    def chunk(
        self, doc_or_text: Document | str, doc_id: str | None = None
    ) -> list[Chunk]:
        """Chunk document using exact token count sliding windows."""
        text, target_id = self._normalize_doc_args(doc_or_text, doc_id)
        if not text:
            return []

        chunks: list[Chunk] = []
        idx = 0
        protected = TextCleaner.extract_protected_blocks(text)
        step_tokens = max(1, self.chunk_size - self.overlap)
        start_char = 0
        text_len = len(text)

        while start_char < text_len:
            low, high, best_end = start_char + 1, text_len, text_len
            while low <= high:
                mid = (low + high) // 2
                if self.count_tokens(text[start_char:mid]) <= self.chunk_size:
                    best_end = mid
                    low = mid + 1
                else:
                    high = mid - 1

            end_char = best_end
            chunk_text = text[start_char:end_char]
            tok_cnt = self.count_tokens(chunk_text)

            if tok_cnt >= self.min_chunk_size or start_char == 0:
                chunks.append(
                    self._create_chunk(
                        target_id, idx, chunk_text, start_char, end_char, tok_cnt, protected
                    )
                )
                idx += 1

            if end_char == text_len:
                break

            low_s, high_s, best_next = start_char + 1, end_char, end_char
            while low_s <= high_s:
                mid = (low_s + high_s) // 2
                if self.count_tokens(text[start_char:mid]) >= step_tokens:
                    best_next = mid
                    high_s = mid - 1
                else:
                    low_s = mid + 1
            start_char = best_next if best_next > start_char else start_char + 1

        return chunks


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

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 0,
        min_chunk_size: int = 50,
        tokenizer: BaseTokenizer | str | None = None,
        separators: list[str] | None = None,
    ) -> None:
        """Initialize recursive structural chunker with separators and tokenizer."""
        super().__init__(
            chunk_size=chunk_size,
            overlap=overlap,
            min_chunk_size=min_chunk_size,
            tokenizer=tokenizer,
        )
        self.separators = (
            list(separators) if separators is not None else list(self.DEFAULT_SEPARATORS)
        )

    def chunk(
        self, doc_or_text: Document | str, doc_id: str | None = None
    ) -> list[Chunk]:
        """Chunk document respecting structural boundaries (headers, paragraphs)."""
        text, target_id = self._normalize_doc_args(doc_or_text, doc_id)
        if not text:
            return []

        protected = TextCleaner.extract_protected_blocks(text)
        leaf_spans = self._partition_text(text, 0, len(text), self.separators)

        candidates: list[tuple[int, int]] = []
        cur_start: int | None = None
        cur_end: int = 0

        for s_start, s_end in leaf_spans:
            if cur_start is None:
                cur_start = s_start
                cur_end = s_end
            else:
                if self.count_tokens(text[cur_start:s_end]) <= self.chunk_size:
                    cur_end = s_end
                else:
                    candidates.append((cur_start, cur_end))
                    ov_start = cur_end
                    if self.overlap > 0:
                        while ov_start > cur_start:
                            sub_txt = text[ov_start:s_end]
                            ov_txt = text[ov_start:cur_end]
                            if (
                                self.count_tokens(sub_txt) <= self.chunk_size
                                and self.count_tokens(ov_txt) <= self.overlap
                            ):
                                break
                            ov_start -= 1
                    cur_start = ov_start
                    cur_end = s_end

        if cur_start is not None:
            candidates.append((cur_start, cur_end))

        chunks: list[Chunk] = []
        idx = 0
        for start_pos, end_pos in candidates:
            content = text[start_pos:end_pos]
            tok_cnt = self.count_tokens(content)

            if tok_cnt >= self.min_chunk_size or idx == 0:
                chunks.append(
                    self._create_chunk(
                        target_id, idx, content, start_pos, end_pos, tok_cnt, protected
                    )
                )
                idx += 1

        return chunks

    def _partition_text(
        self, text: str, start: int, end: int, separators: list[str]
    ) -> list[tuple[int, int]]:
        """Recursively partition text slice [start:end] into spans <= chunk_size."""
        slice_text = text[start:end]
        if not slice_text:
            return []
        if self.count_tokens(slice_text) <= self.chunk_size:
            return [(start, end)]

        sep_found: str | None = None
        sep_idx = -1
        for i, sep in enumerate(separators):
            if sep in slice_text:
                sep_found = sep
                sep_idx = i
                break

        if sep_found is None:
            return self._fallback_spans(text, start, end)

        parts = slice_text.split(sep_found)
        rem_seps = separators[sep_idx + 1 :]
        spans: list[tuple[int, int]] = []
        cur_pos = start

        for i, part in enumerate(parts):
            p_len = len(part) if i == 0 else len(sep_found) + len(part)
            p_start = cur_pos
            p_end = cur_pos + p_len
            cur_pos = p_end

            if p_start < p_end:
                spans.extend(self._partition_text(text, p_start, p_end, rem_seps))

        return spans if spans else [(start, end)]

    def _fallback_spans(
        self, text: str, start: int, end: int
    ) -> list[tuple[int, int]]:
        """Fallback binary search for character spans exceeding chunk_size."""
        spans: list[tuple[int, int]] = []
        cur = start
        while cur < end:
            low, high, best = cur + 1, end, cur + 1
            while low <= high:
                mid = (low + high) // 2
                if self.count_tokens(text[cur:mid]) <= self.chunk_size:
                    best = mid
                    low = mid + 1
                else:
                    high = mid - 1
            spans.append((cur, best))
            cur = best
        return spans
