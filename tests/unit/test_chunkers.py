"""Unit tests for fixed and recursive chunking strategies and model-agnostic tokenizers."""

import pytest

from ingestion.chunkers import (
    ChunkingStrategy,
    FixedSizeChunker,
    RecursiveStructuralChunker,
)
from ingestion.exceptions import ChunkError
from ingestion.models import Document
from ingestion.tokenizers import GeminiEncoder, TiktokenEncoder


def test_chunker_with_injected_gemini_encoder(sample_document: Document) -> None:
    """Verify FixedSizeChunker and RecursiveStructuralChunker operate cleanly with injected GeminiEncoder."""
    gemini_enc = GeminiEncoder("gemini-1.5-flash")
    fixed_chunker = FixedSizeChunker(chunk_size=30, overlap=5, min_chunk_size=10, tokenizer=gemini_enc)
    rec_chunker = RecursiveStructuralChunker(chunk_size=50, min_chunk_size=10, tokenizer=gemini_enc)

    fixed_chunks = fixed_chunker.chunk(sample_document)
    rec_chunks = rec_chunker.chunk(sample_document)

    assert len(fixed_chunks) > 0
    assert len(rec_chunks) > 0
    assert all(c.token_count == gemini_enc.count_tokens(c.content) for c in fixed_chunks)
    assert all(c.token_count == gemini_enc.count_tokens(c.content) for c in rec_chunks)


def test_chunking_strategy_parameter_validations() -> None:
    """Verify ChunkingStrategy validates parameters."""
    with pytest.raises(ChunkError, match="chunk_size must be positive"):
        FixedSizeChunker(chunk_size=0)

    with pytest.raises(ChunkError, match="overlap must be non-negative"):
        FixedSizeChunker(chunk_size=100, overlap=-10)

    with pytest.raises(ChunkError, match="overlap must be strictly smaller"):
        FixedSizeChunker(chunk_size=50, overlap=50)

    with pytest.raises(ChunkError, match="min_chunk_size must be non-negative"):
        FixedSizeChunker(chunk_size=100, overlap=10, min_chunk_size=-5)


def test_chunking_strategy_raw_string_input() -> None:
    """Verify strategy chunk method accepts raw string with doc_id."""
    chunker = FixedSizeChunker(chunk_size=100, overlap=10, min_chunk_size=5)
    raw_text = "This is raw text without LoadedDocument wrapper."
    chunks = chunker.chunk(raw_text, doc_id="raw_doc_123")
    assert len(chunks) > 0
    assert chunks[0].doc_id == "raw_doc_123"
    assert chunks[0].token_count == chunker.count_tokens(chunks[0].content)


def test_fixed_size_chunker(sample_document: Document) -> None:
    """Verify FixedSizeChunker produces chunks within character boundaries."""
    tiktoken_enc = TiktokenEncoder("cl100k_base")
    chunker = FixedSizeChunker(chunk_size=30, overlap=5, min_chunk_size=10, tokenizer=tiktoken_enc)
    chunks = chunker.chunk(sample_document)
    assert len(chunks) > 0
    assert all(c.doc_id == sample_document.id for c in chunks)
    assert all(c.token_count == chunker.count_tokens(c.content) for c in chunks)


def test_chunking_strategy_inheritance() -> None:
    """Verify strategy implementations inherit from ChunkingStrategy."""
    fixed = FixedSizeChunker(chunk_size=100)
    rec = RecursiveStructuralChunker(chunk_size=100)
    assert isinstance(fixed, ChunkingStrategy)
    assert isinstance(rec, ChunkingStrategy)


def test_recursive_chunker(sample_document: Document) -> None:
    """Verify RecursiveStructuralChunker preserves document structural integrity."""
    chunker = RecursiveStructuralChunker(chunk_size=50, min_chunk_size=10, tokenizer="gemini")
    chunks = chunker.chunk(sample_document)
    assert len(chunks) > 0
    assert not any(c.is_orphan_block for c in chunks)
    assert all(c.token_count == chunker.count_tokens(c.content) for c in chunks)


def test_fixed_size_token_chunker_exact_counts() -> None:
    """Verify FixedSizeChunker enforces exact token limits and token overlaps."""
    encoder = TiktokenEncoder("cl100k_base")
    chunker = FixedSizeChunker(chunk_size=20, overlap=5, min_chunk_size=5, tokenizer=encoder)
    text = "This is a detailed synthetic text document designed to test exact token counts. " * 4
    chunks = chunker.chunk(text, doc_id="exact_doc")

    assert len(chunks) > 1
    assert all(c.token_count <= 20 for c in chunks)
    for c in chunks[:-1]:
        assert c.token_count == 20
    assert all(text[c.start_char:c.end_char] == c.content for c in chunks)


def test_fixed_size_token_chunker_empty_input() -> None:
    """Verify FixedSizeChunker returns an empty list for empty input text."""
    chunker = FixedSizeChunker(chunk_size=50, overlap=10)
    assert chunker.chunk("") == []


def test_fixed_size_token_chunker_orphan_detection() -> None:
    """Verify FixedSizeChunker flags orphan blocks when Markdown tables are split."""
    encoder = TiktokenEncoder("cl100k_base")
    chunker = FixedSizeChunker(chunk_size=15, overlap=3, min_chunk_size=5, tokenizer=encoder)
    table_text = "Header\n\n| Col A | Col B |\n| --- | --- |\n| Val A1 | Val B1 |\n| Val A2 | Val B2 |\n\nFooter"
    chunks = chunker.chunk(table_text, doc_id="table_doc")

    assert len(chunks) > 1
    assert any(c.is_orphan_block for c in chunks)


def test_recursive_structural_chunker_custom_separators() -> None:
    """Verify RecursiveStructuralChunker respects custom separator hierarchy."""
    custom_seps = ["\n\n", "\n", " "]
    chunker = RecursiveStructuralChunker(
        chunk_size=15, min_chunk_size=5, separators=custom_seps
    )
    assert chunker.separators == custom_seps

    text = "Paragraph 1 line text.\n\nParagraph 2 line text."
    chunks = chunker.chunk(text, doc_id="custom_sep_doc")
    assert len(chunks) > 0
    assert all(c.token_count <= 15 for c in chunks)


def test_recursive_structural_chunker_empty_input() -> None:
    """Verify RecursiveStructuralChunker returns empty list for empty string."""
    chunker = RecursiveStructuralChunker(chunk_size=50)
    assert chunker.chunk("") == []


def test_recursive_structural_chunker_markdown_hierarchy() -> None:
    """Verify RecursiveStructuralChunker preserves markdown section boundaries."""
    doc_content = (
        "# Title Section\n\n"
        "This is the introduction paragraph under the title section.\n\n"
        "## SubSection A\n\n"
        "Content inside subsection A detailing structural splitting rules.\n\n"
        "### Deep Section B\n\n"
        "Deep section content testing sentence and word level fallback."
    )
    chunker = RecursiveStructuralChunker(chunk_size=20, min_chunk_size=5)
    chunks = chunker.chunk(doc_content, doc_id="struct_doc")

    assert len(chunks) > 1
    assert all(c.token_count <= 20 for c in chunks)
    assert all(doc_content[c.start_char:c.end_char] == c.content for c in chunks)






