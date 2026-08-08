"""Chunking strategies using dependency-injected model-agnostic tokenizers."""

from abc import ABC, abstractmethod

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

    @abstractmethod
    def chunk(
        self, doc_or_text: Document | str, doc_id: str | None = None
    ) -> list[Chunk]:
        """Split document or text into typed Chunk objects."""
        pass


BaseChunker = ChunkingStrategy


class FixedSizeChunker(ChunkingStrategy):
    """Rigid fixed-length character window chunker with fixed overlap."""

    def chunk(
        self, doc_or_text: Document | str, doc_id: str | None = None
    ) -> list[Chunk]:
        """Chunk document using rigid character windows."""
        text, target_id = self._normalize_doc_args(doc_or_text, doc_id)
        chunks: list[Chunk] = []
        start = 0
        idx = 0
        protected_blocks = TextCleaner.extract_protected_blocks(text)

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]

            if len(chunk_text.strip()) >= self.min_chunk_size or start == 0:
                is_orphan = any(
                    (p_start < end < p_end and start <= p_start)
                    for p_start, p_end, _ in protected_blocks
                )
                chunk_obj = Chunk(
                    id=f"{target_id}_chk_{idx}",
                    doc_id=target_id,
                    chunk_index=idx,
                    content=chunk_text,
                    start_char=start,
                    end_char=end,
                    token_count=self.count_tokens(chunk_text),
                    is_orphan_block=is_orphan,
                )
                chunks.append(chunk_obj)
                idx += 1

            if end == len(text):
                break
            start += self.chunk_size - self.overlap

        return chunks


class RecursiveStructuralChunker(ChunkingStrategy):
    """Context-aware recursive chunker respecting Markdown boundaries and tables."""

    def chunk(
        self, doc_or_text: Document | str, doc_id: str | None = None
    ) -> list[Chunk]:
        """Chunk document respecting structural boundaries (headers, paragraphs)."""
        text, target_id = self._normalize_doc_args(doc_or_text, doc_id)
        chunks: list[Chunk] = []
        separators = ["\n# ", "\n## ", "\n### ", "\n\n", "\n", " "]
        raw_blocks = self._split_recursive(text, separators, self.chunk_size)

        idx = 0
        current_offset = 0
        for block in raw_blocks:
            block_len = len(block)
            start_pos = text.find(block, current_offset)
            if start_pos == -1:
                start_pos = current_offset
            end_pos = start_pos + block_len
            current_offset = end_pos

            if len(block.strip()) >= self.min_chunk_size:
                chunk_obj = Chunk(
                    id=f"{target_id}_chk_{idx}",
                    doc_id=target_id,
                    chunk_index=idx,
                    content=block,
                    start_char=start_pos,
                    end_char=end_pos,
                    token_count=self.count_tokens(block),
                    is_orphan_block=False,
                )
                chunks.append(chunk_obj)
                idx += 1

        return chunks

    def _split_recursive(self, text: str, separators: list[str], max_len: int) -> list[str]:
        """Recursive helper splitting text across structural separators."""
        if len(text) <= max_len or not separators:
            return [text]

        sep = separators[0]
        remaining_seps = separators[1:]
        parts = text.split(sep)
        result: list[str] = []

        for i, part in enumerate(parts):
            piece = part if i == 0 else sep + part
            if len(piece) > max_len:
                sub_parts = self._split_recursive(piece, remaining_seps, max_len)
                result.extend(sub_parts)
            else:
                result.append(piece)

        return result



