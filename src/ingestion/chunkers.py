"""Chunking strategies using the Strategy Pattern."""

import uuid
from abc import ABC, abstractmethod

from ingestion.cleaner import TextCleaner
from ingestion.models import Chunk, Document


class BaseChunker(ABC):
    """Abstract Base Class for document chunking strategies."""

    def __init__(self, chunk_size: int = 512, overlap: int = 64, min_chunk_size: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

    @abstractmethod
    def chunk(self, doc: Document) -> list[Chunk]:
        """Split document into text chunks."""
        pass


class FixedSizeChunker(BaseChunker):
    """Rigid fixed-length character window chunker with fixed overlap."""

    def chunk(self, doc: Document) -> list[Chunk]:
        """Chunk document using rigid character windows."""
        text = doc.content
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
                    id=f"{doc.id}_chk_{idx}",
                    doc_id=doc.id,
                    chunk_index=idx,
                    content=chunk_text,
                    start_char=start,
                    end_char=end,
                    token_count=len(chunk_text.split()),
                    is_orphan_block=is_orphan,
                )
                chunks.append(chunk_obj)
                idx += 1

            if end == len(text):
                break
            start += self.chunk_size - self.overlap

        return chunks


class RecursiveStructuralChunker(BaseChunker):
    """Context-aware recursive chunker respecting Markdown boundaries and tables."""

    def chunk(self, doc: Document) -> list[Chunk]:
        """Chunk document respecting structural boundaries (headers, paragraphs)."""
        text = doc.content
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
                    id=f"{doc.id}_chk_{idx}",
                    doc_id=doc.id,
                    chunk_index=idx,
                    content=block,
                    start_char=start_pos,
                    end_char=end_pos,
                    token_count=len(block.split()),
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
