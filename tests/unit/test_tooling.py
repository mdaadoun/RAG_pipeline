"""Unit tests for Step 1.2 tooling and code quality setup."""

from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


def test_ruff_config_exists_and_valid() -> None:
    """Verify ruff.toml exists and parses as valid TOML configuration."""
    ruff_path = Path("ruff.toml")
    assert ruff_path.exists(), "ruff.toml must exist at project root"

    content = ruff_path.read_text(encoding="utf-8")
    assert "target-version = \"py311\"" in content
    assert "[lint]" in content

    if tomllib is not None:
        with open(ruff_path, "rb") as f:
            config = tomllib.load(f)
        assert config.get("target-version") == "py311"
        assert "lint" in config


def test_pyproject_mypy_strict_mode() -> None:
    """Verify pyproject.toml configures mypy in strict mode."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml must exist at project root"

    content = pyproject_path.read_text(encoding="utf-8")
    assert "[tool.mypy]" in content
    assert "strict = true" in content
    assert "disallow_untyped_defs = true" in content

    if tomllib is not None:
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)
        mypy_config = config.get("tool", {}).get("mypy", {})
        assert mypy_config.get("strict") is True


def test_makefile_targets_defined() -> None:
    """Verify Makefile contains expected standard shortcuts."""
    makefile_path = Path("Makefile")
    assert makefile_path.exists(), "Makefile must exist at project root"

    content = makefile_path.read_text(encoding="utf-8")
    for target in ["install:", "lint:", "test:", "dev:", "clean:"]:
        assert target in content, f"Makefile missing target {target}"
