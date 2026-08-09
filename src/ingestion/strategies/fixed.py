"""Fixed-size token sliding window chunker."""

from ingestion.cleaner import TextCleaner
from ingestion.models import Chunk, Document
from ingestion.strategies.base import ChunkingStrategy


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
