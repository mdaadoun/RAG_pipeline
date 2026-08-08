"""Unit tests for text and markdown document loaders."""

from pathlib import Path

import pytest

from ingestion.exceptions import DocumentLoadError
from ingestion.loaders import (
    DocumentLoader,
    MarkdownLoader,
    TextLoader,
    TextMarkdownLoader,
    compute_document_id,
    get_loader,
)


def test_document_loader_abc_instantiation() -> None:
    """Verify DocumentLoader ABC cannot be instantiated directly."""
    with pytest.raises(TypeError):
        DocumentLoader()



def test_markdown_loader(fixtures_dir: Path) -> None:
    """Verify MarkdownLoader parses markdown file correctly."""
    file_path = fixtures_dir / "01_clean_doc.md"
    loader = MarkdownLoader(file_path)
    doc = loader.load()
    assert doc.metadata["format"] == "markdown"
    assert doc.metadata["filename"] == "01_clean_doc.md"
    assert doc.metadata["file_size_bytes"] > 0
    assert "Architecture Overview" in doc.content
    assert doc.id.startswith("doc_")


def test_text_loader(fixtures_dir: Path) -> None:
    """Verify TextLoader parses plain text file correctly."""
    file_path = fixtures_dir / "02_noisy_header.txt"
    loader = TextLoader(file_path)
    doc = loader.load()
    assert doc.metadata["format"] == "txt"
    assert doc.metadata["filename"] == "02_noisy_header.txt"
    assert doc.metadata["file_size_bytes"] > 0
    assert doc.char_count > 0
    assert doc.id.startswith("doc_")


def test_text_markdown_loader_auto_detect(fixtures_dir: Path) -> None:
    """Verify TextMarkdownLoader auto-detects text vs markdown format."""
    md_loader = TextMarkdownLoader(fixtures_dir / "01_clean_doc.md")
    md_doc = md_loader.load()
    assert md_doc.metadata["format"] == "markdown"

    txt_loader = TextMarkdownLoader(fixtures_dir / "02_noisy_header.txt")
    txt_doc = txt_loader.load()
    assert txt_doc.metadata["format"] == "txt"


def test_deterministic_document_id() -> None:
    """Verify document ID is deterministically computed from filename and content."""
    id1 = compute_document_id("sample.md", "# Hello World")
    id2 = compute_document_id("sample.md", "# Hello World")
    id3 = compute_document_id("sample.md", "# Different Content")

    assert id1 == id2
    assert id1 != id3
    assert id1.startswith("doc_")


def test_loader_file_not_found() -> None:
    """Verify DocumentLoadError is raised when source file does not exist."""
    loader = TextLoader("non_existent_file.txt")
    with pytest.raises(DocumentLoadError) as exc_info:
        loader.load()
    assert "Source file not found" in str(exc_info.value)
    assert exc_info.value.details["file_path"] == "non_existent_file.txt"


def test_loader_invalid_encoding(tmp_path: Path) -> None:
    """Verify DocumentLoadError is raised on non-UTF-8 binary data."""
    binary_file = tmp_path / "bad_encoding.bin"
    binary_file.write_bytes(b"\x80\x81\xff\xfe")

    loader = TextLoader(binary_file)
    with pytest.raises(DocumentLoadError) as exc_info:
        loader.load()
    assert "Failed to read file" in str(exc_info.value)


def test_get_loader_factory(fixtures_dir: Path, tmp_path: Path) -> None:
    """Verify get_loader returns correct loader instance based on extension."""
    md_loader = get_loader(fixtures_dir / "01_clean_doc.md")
    assert isinstance(md_loader, MarkdownLoader)

    txt_loader = get_loader(fixtures_dir / "02_noisy_header.txt")
    assert isinstance(txt_loader, TextLoader)

    pdf_file = tmp_path / "doc.pdf"
    pdf_file.touch()
    with pytest.raises(DocumentLoadError) as exc_info:
        get_loader(pdf_file)
    assert "Unsupported file format" in str(exc_info.value)

