"""Unit tests for package directory structure creation & package exports."""

from pathlib import Path

import ingestion
from ingestion.exceptions import (
    AuditError,
    ChunkError,
    CleanError,
    DocumentLoadError,
    IngestionError,
)


def test_package_directory_structure_exists() -> None:
    """Verify package modules exist under src/ingestion/."""
    base_dir = Path(__file__).parent.parent.parent / "src" / "ingestion"
    required_files = [
        "__init__.py",
        "models.py",
        "exceptions.py",
        "loaders.py",
        "cleaner.py",
        "tokenizers.py",
        "chunkers.py",
        "detector.py",
        "monitor.py",
        "pipeline.py",
        "cli.py",
    ]
    for filename in required_files:
        filepath = base_dir / filename
        assert filepath.exists(), f"Missing required package file: {filepath}"


def test_test_directories_exist() -> None:
    """Verify required test directory hierarchy exists."""
    tests_dir = Path(__file__).parent.parent
    required_dirs = ["unit", "integration", "fixtures"]
    for dirname in required_dirs:
        dirpath = tests_dir / dirname
        assert dirpath.is_dir(), f"Missing required test directory: {dirpath}"


def test_custom_exception_hierarchy() -> None:
    """Verify custom exception hierarchy inheritance and instantiation."""
    base_err = IngestionError("Base error")
    assert isinstance(base_err, Exception)

    load_err = DocumentLoadError("Load failed")
    assert isinstance(load_err, IngestionError)

    clean_err = CleanError("Clean failed")
    assert isinstance(clean_err, IngestionError)

    chunk_err = ChunkError("Chunk failed")
    assert isinstance(chunk_err, IngestionError)

    audit_err = AuditError("Audit failed")
    assert isinstance(audit_err, IngestionError)


def test_package_exports() -> None:
    """Verify root ingestion package exports core domain models, exceptions, loaders, and tokenizers."""
    expected_exports = [
        "BaseDomainModel",
        "StrategyType",
        "TokenizerType",
        "IngestionConfig",
        "LoadedDocument",
        "Document",
        "Chunk",
        "DocumentReport",
        "IngestionMetrics",
        "IngestionReport",
        "AuditReport",
        "IngestionError",
        "DocumentLoadError",
        "CleanError",
        "ChunkError",
        "AuditError",
        "DocumentLoader",
        "TextLoader",
        "MarkdownLoader",
        "TextMarkdownLoader",
        "get_loader",
        "compute_document_id",
        "TextCleaner",
        "BaseTokenizer",
        "TiktokenEncoder",
        "GeminiEncoder",
        "HeuristicTokenizer",
        "get_tokenizer",
        "ChunkingStrategy",
        "BaseChunker",
        "FixedSizeChunker",
        "RecursiveStructuralChunker",
        "OrphanBlockDetector",
        "StructuralBlock",
    ]
    for symbol in expected_exports:
        assert hasattr(ingestion, symbol), f"Package missing export: {symbol}"



