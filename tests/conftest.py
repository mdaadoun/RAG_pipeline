"""Pytest fixtures for unit and integration testing."""

from pathlib import Path

import pytest
from ingestion.models import Document


@pytest.fixture
def sample_document() -> Document:
    """Fixture providing a standard test document."""
    return Document(
        id="doc_test_01",
        file_path="tests/fixtures/01_clean_doc.md",
        content="# Test Document\n\nThis is a sample document for testing chunkers.",
        metadata={"format": "markdown"},
    )


@pytest.fixture
def fixtures_dir() -> Path:
    """Fixture providing path to test fixtures folder."""
    return Path(__file__).parent / "fixtures"
