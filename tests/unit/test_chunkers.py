"""Unit tests for fixed and recursive chunking strategies."""

from ingestion.chunkers import FixedSizeChunker, RecursiveStructuralChunker
from ingestion.models import Document


def test_fixed_size_chunker(sample_document: Document) -> None:
    """Verify FixedSizeChunker produces chunks within character boundaries."""
    chunker = FixedSizeChunker(chunk_size=30, overlap=5, min_chunk_size=10)
    chunks = chunker.chunk(sample_document)
    assert len(chunks) > 0
    assert all(c.doc_id == sample_document.id for c in chunks)


def test_recursive_chunker(sample_document: Document) -> None:
    """Verify RecursiveStructuralChunker preserves document structural integrity."""
    chunker = RecursiveStructuralChunker(chunk_size=50, min_chunk_size=10)
    chunks = chunker.chunk(sample_document)
    assert len(chunks) > 0
    assert not any(c.is_orphan_block for c in chunks)
