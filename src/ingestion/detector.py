"""Orphan block detector for identifying Markdown structural boundary splits."""

import re
from typing import NamedTuple

from ingestion.models import Chunk


class StructuralBlock(NamedTuple):
    """Immutable representation of a document structural block range."""

    block_type: str
    start_char: int
    end_char: int
    content: str


class OrphanBlockDetector:
    """Scanner for detecting Markdown tables and code blocks split across chunk boundaries."""

    def __init__(self) -> None:
        """Initialize block pattern regexes for Markdown tables, code, and math blocks."""
        self._patterns: list[tuple[str, re.Pattern[str]]] = [
            ("table", re.compile(r"(?:^|\n)(\|[^\n]+\|\n?)+", re.MULTILINE)),
            ("code_block", re.compile(r"```[\s\S]*?```|~~~[\s\S]*?~~~")),
            ("math_block", re.compile(r"\$\$[\s\S]*?\$\$")),
        ]

    def extract_structural_blocks(self, text: str) -> list[StructuralBlock]:
        """Extract all structural blocks from text with start and end character offsets."""
        if not text:
            return []
        blocks: list[StructuralBlock] = []
        for b_type, pattern in self._patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                blocks.append(
                    StructuralBlock(
                        block_type=b_type,
                        start_char=start,
                        end_char=end,
                        content=match.group(0),
                    )
                )
        return blocks

    def detect_orphan_blocks(self, cleaned_text: str, chunks: list[Chunk]) -> int:
        """Count structural blocks severed across chunk boundaries without full single-chunk coverage."""
        if not cleaned_text or not chunks:
            return 0

        blocks = self.extract_structural_blocks(cleaned_text)
        orphan_count = 0

        for block in blocks:
            intersecting = [
                c
                for c in chunks
                if c.start_char < block.end_char and c.end_char > block.start_char
            ]
            if intersecting:
                preserved = any(
                    c.start_char <= block.start_char and c.end_char >= block.end_char
                    for c in intersecting
                )
                if not preserved:
                    orphan_count += 1

        return orphan_count

    def is_orphan_chunk(self, chunk: Chunk, cleaned_text: str) -> bool:
        """Determine if a single chunk contains a severed structural block fragment."""
        if chunk.is_orphan_block:
            return True
        if not cleaned_text:
            return False
        blocks = self.extract_structural_blocks(cleaned_text)
        for block in blocks:
            intersects = (
                chunk.start_char < block.end_char and chunk.end_char > block.start_char
            )
            fully_contains = (
                chunk.start_char <= block.start_char and chunk.end_char >= block.end_char
            )
            if intersects and not fully_contains:
                return True
        return False
