"""Unit tests for Step 1.1 environment initialization & configuration."""

import pydantic
import structlog
import tiktoken

from config.logging import get_logger, setup_logging
from config.settings import Settings, get_settings


def test_environment_settings_defaults() -> None:
    """Verify default application settings initialization and values."""
    settings = Settings()
    assert settings.env in ["development", "staging", "production"]
    assert settings.log_level == "INFO"
    assert settings.default_chunk_size == 512
    assert settings.default_overlap == 64
    assert settings.character_coverage_threshold == 0.98


def test_get_settings_caching() -> None:
    """Verify get_settings returns a cached LRU Settings instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_logging_setup() -> None:
    """Verify structured logging initialization and logger retrieval."""
    setup_logging("DEBUG")
    logger = get_logger("test_env")
    assert logger is not None


def test_core_dependencies_available() -> None:
    """Verify required third-party core dependencies are installed and importable."""
    assert hasattr(pydantic, "__version__")
    assert hasattr(structlog, "__version__")
    enc = tiktoken.get_encoding("cl100k_base")
    assert enc is not None
    tokens = enc.encode("Environment setup test")
    assert len(tokens) > 0
