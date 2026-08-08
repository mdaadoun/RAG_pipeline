"""Unit tests for text and markdown document loaders."""

from pathlib import Path

from ingestion.loaders import MarkdownLoader, TextLoader


def test_markdown_loader(fixtures_dir: Path) -> None:
    """Verify MarkdownLoader parses markdown file correctly."""
    file_path = fixtures_dir / "01_clean_doc.md"
    loader = MarkdownLoader(file_path)
    doc = loader.load()
    assert doc.metadata["format"] == "markdown"
    assert "Architecture Overview" in doc.content


def test_text_loader(fixtures_dir: Path) -> None:
    """Verify TextLoader parses plain text file correctly."""
    file_path = fixtures_dir / "02_noisy_header.txt"
    loader = TextLoader(file_path)
    doc = loader.load()
    assert doc.metadata["format"] == "txt"
    assert doc.char_count > 0
