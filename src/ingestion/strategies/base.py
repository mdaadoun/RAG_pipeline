"""Base chunking strategy interface and common utilities."""

from abc import ABC, abstractmethod

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
