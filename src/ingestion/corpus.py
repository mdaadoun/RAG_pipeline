"""Synthetic test corpus loader and management module."""

from pathlib import Path
from typing import Final

from pydantic import Field

from ingestion.exceptions import DocumentLoadError
from ingestion.models import BaseDomainModel

DEFAULT_FIXTURES: Final[dict[str, dict[str, str]]] = {
    "01_clean_doc.md": {
        "category": "clean",
        "description": "Clean Markdown document testing standard ingestion, high coverage, and 0 orphan blocks.",
        "expected_behavior": "Passes audit with coverage >= 98% and 0 orphan blocks.",
        "content": (
            "# Architecture Overview\n\n"
            "This is a clean markdown document used for testing standard ingestion "
            "and chunking functionality.\n\n"
            "## Core Features\n\n"
            "- Clean structural headers\n"
            "- Standard paragraphs with clear semantic intent\n"
            "- High character retention\n"
        ),
    },
    "02_noisy_header.txt": {
        "category": "noisy",
        "description": "Raw text with repeated system header noise and control character artifacts.",
        "expected_behavior": "Normalizes whitespace and strips control characters during cleaning.",
        "content": (
            "=== SYSTEM HEADER NOISE ===\n"
            "Date: 2026-08-08\n"
            "Author: Automated System\n\n"
            "This is raw text with control characters\x00 and trailing space noise.  \n"
            "It tests the cleaning layer normalization capabilities.\n"
        ),
    },
    "03_table_split.md": {
        "category": "table_split",
        "description": "Markdown containing structured tables and code blocks.",
        "expected_behavior": "Triggers orphan blocks under fixed-size chunking; stays intact under recursive structural chunking.",
        "content": (
            "# Tabular Data Sample\n\n"
            "Below is a critical table that should not be split across chunks.\n\n"
            "| Metric | Target | Status |\n"
            "| --- | --- | --- |\n"
            "| Coverage | 98% | Passing |\n"
            "| Orphans | 0 | Passing |\n\n"
            "```python\n"
            "def example():\n"
            '    return "Code block protection"\n'
            "```\n"
        ),
    },
    "04_corrupted_encoding.txt": {
        "category": "corrupted_encoding",
        "description": "Document with non-standard Unicode characters testing NFKC normalization.",
        "expected_behavior": "Normalizes accented and composite Unicode characters without failing loader.",
        "content": (
            "Corrupted document test file with non-standard Unicode: Caf\u00e9 & Na\u00efve testing NFKC.\n"
        ),
    },
}


class SyntheticFixtureSpec(BaseDomainModel):
    """Immutable metadata specification for a synthetic test fixture."""

    name: str = Field(..., description="Filename of the synthetic fixture")
    category: str = Field(..., description="Fixture error or test classification")
    description: str = Field(..., description="Human-readable description of fixture purpose")
    expected_behavior: str = Field(..., description="Expected pipeline outcome for fixture")
    file_path: Path | None = Field(default=None, description="Absolute or relative filesystem path")


class SyntheticCorpus(BaseDomainModel):
    """Synthetic test corpus manager for benchmark fixtures."""

    fixtures_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "tests" / "fixtures"
    )

    def list_fixtures(self) -> list[SyntheticFixtureSpec]:
        """Return list of synthetic fixture specifications."""
        fixtures: list[SyntheticFixtureSpec] = []
        for name, meta in DEFAULT_FIXTURES.items():
            path = self.fixtures_dir / name
            fixtures.append(
                SyntheticFixtureSpec(
                    name=name,
                    category=meta["category"],
                    description=meta["description"],
                    expected_behavior=meta["expected_behavior"],
                    file_path=path if path.exists() else None,
                )
            )
        return fixtures

    def get_fixture_path(self, name: str) -> Path:
        """Get filesystem path for named fixture, ensuring existence."""
        if name not in DEFAULT_FIXTURES:
            raise DocumentLoadError(
                f"Unknown synthetic fixture name: '{name}'",
                details={"available": list(DEFAULT_FIXTURES.keys())},
            )
        path = self.fixtures_dir / name
        if not path.exists():
            self.ensure_default_fixtures()
        return path

    def load_fixture_content(self, name: str) -> str:
        """Load text content of named fixture from disk."""
        path = self.get_fixture_path(name)
        try:
            return path.read_text(encoding="utf-8")
        except Exception as err:
            raise DocumentLoadError(
                f"Failed to read synthetic fixture content for '{name}': {err}",
                details={"path": str(path), "error": str(err)},
            ) from err

    def ensure_default_fixtures(self) -> dict[str, Path]:
        """Ensure default test fixtures exist on disk, creating them if missing."""
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        created_paths: dict[str, Path] = {}
        for name, meta in DEFAULT_FIXTURES.items():
            path = self.fixtures_dir / name
            if not path.exists():
                path.write_text(meta["content"], encoding="utf-8")
            created_paths[name] = path
        return created_paths

    def validate_corpus(self) -> dict[str, bool]:
        """Validate integrity and accessibility of all synthetic fixtures."""
        results: dict[str, bool] = {}
        for name in DEFAULT_FIXTURES:
            path = self.fixtures_dir / name
            results[name] = path.exists() and path.is_file() and path.stat().st_size > 0
        return results
