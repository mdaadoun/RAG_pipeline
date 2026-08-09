"""Unit tests for synthetic test corpus management module."""

from pathlib import Path

import pytest

from ingestion.corpus import (
    DEFAULT_FIXTURES,
    SyntheticCorpus,
    SyntheticFixtureSpec,
)
from ingestion.exceptions import DocumentLoadError


def test_synthetic_fixture_spec_model() -> None:
    """Verify SyntheticFixtureSpec model instantiation and properties."""
    spec = SyntheticFixtureSpec(
        name="01_clean_doc.md",
        category="clean",
        description="Clean document test fixture",
        expected_behavior="Pass audit cleanly",
    )
    assert spec.name == "01_clean_doc.md"
    assert spec.category == "clean"
    assert spec.file_path is None


def test_synthetic_corpus_list_fixtures(tmp_path: Path) -> None:
    """Verify list_fixtures returns specs for all 4 default fixtures."""
    corpus = SyntheticCorpus(fixtures_dir=tmp_path)
    corpus.ensure_default_fixtures()
    fixtures = corpus.list_fixtures()
    assert len(fixtures) == 4
    names = {f.name for f in fixtures}
    assert names == {
        "01_clean_doc.md",
        "02_noisy_header.txt",
        "03_table_split.md",
        "04_corrupted_encoding.txt",
    }
    for spec in fixtures:
        assert spec.file_path is not None
        assert spec.file_path.exists()


def test_synthetic_corpus_get_fixture_path(tmp_path: Path) -> None:
    """Verify get_fixture_path auto-creates fixtures if missing and returns path."""
    corpus = SyntheticCorpus(fixtures_dir=tmp_path)
    path = corpus.get_fixture_path("01_clean_doc.md")
    assert path.exists()
    assert path.name == "01_clean_doc.md"


def test_synthetic_corpus_unknown_fixture_raises_error(tmp_path: Path) -> None:
    """Verify get_fixture_path raises DocumentLoadError for unknown fixture."""
    corpus = SyntheticCorpus(fixtures_dir=tmp_path)
    with pytest.raises(DocumentLoadError, match="Unknown synthetic fixture name"):
        corpus.get_fixture_path("non_existent_fixture.md")


def test_synthetic_corpus_load_fixture_content(tmp_path: Path) -> None:
    """Verify load_fixture_content returns valid fixture content."""
    corpus = SyntheticCorpus(fixtures_dir=tmp_path)
    corpus.ensure_default_fixtures()
    content = corpus.load_fixture_content("03_table_split.md")
    assert "Tabular Data Sample" in content
    assert "| Metric | Target | Status |" in content


def test_synthetic_corpus_validate_corpus(tmp_path: Path) -> None:
    """Verify validate_corpus returns true status for all existing non-empty fixtures."""
    corpus = SyntheticCorpus(fixtures_dir=tmp_path)
    corpus.ensure_default_fixtures()
    status_map = corpus.validate_corpus()
    assert len(status_map) == 4
    assert all(status_map.values())


def test_default_fixtures_dictionary_completeness() -> None:
    """Verify DEFAULT_FIXTURES contains exact required roadmap files and categories."""
    required_files = [
        "01_clean_doc.md",
        "02_noisy_header.txt",
        "03_table_split.md",
        "04_corrupted_encoding.txt",
    ]
    for filename in required_files:
        assert filename in DEFAULT_FIXTURES
        meta = DEFAULT_FIXTURES[filename]
        assert "category" in meta
        assert "description" in meta
        assert "expected_behavior" in meta
        assert "content" in meta
