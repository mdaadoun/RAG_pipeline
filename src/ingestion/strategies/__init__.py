"""Strategy pattern package for chunking algorithms."""

from ingestion.strategies.base import BaseChunker, ChunkingStrategy
from ingestion.strategies.fixed import FixedSizeChunker
from ingestion.strategies.recursive import RecursiveStructuralChunker

__all__ = [
    "BaseChunker",
    "ChunkingStrategy",
    "FixedSizeChunker",
    "RecursiveStructuralChunker",
]
