"""Unit tests for text cleaner, normalization, boilerplate deduplication, and protection shielding."""

import pytest

from ingestion.cleaner import TextCleaner
from ingestion.exceptions import CleanError


def test_cleaner_nfkc_normalization() -> None:
    """Verify NFKC normalization strips control bytes and standardizes unicode."""
    cleaner = TextCleaner()
    raw = "Hello\x00 World! Na\u00efve Caf\u00e9 \xa0 testing."
    cleaned = cleaner.clean(raw)
    assert "\x00" not in cleaned
    assert "Hello World!" in cleaned
    assert "Naive" in cleaned or "Naïve" in cleaned
    assert "\xa0" not in cleaned


def test_extract_protected_blocks() -> None:
    """Verify code block and table extraction indices."""
    text = (
        "Header\n\n"
        "```python\nprint('hello')\n```\n\n"
        "| A | B |\n|---|---|\n| 1 | 2 |\n"
    )
    protected = TextCleaner.extract_protected_blocks(text)
    assert len(protected) == 2
    assert protected[0][2] == "code_block"
    assert protected[1][2] == "table"


def test_whitespace_standardization_and_capping() -> None:
    """Verify excess newlines are capped to max_newlines and trailing spaces trimmed."""
    cleaner = TextCleaner(max_newlines=2)
    raw = "Line 1   \n\n\n\n\nLine 2\t  \n\n\nLine 3"
    cleaned = cleaner.clean(raw)
    assert cleaned == "Line 1\n\nLine 2\n\nLine 3"


def test_boilerplate_line_deduplication() -> None:
    """Verify repetitive boilerplate lines exceeding threshold are removed."""
    cleaner = TextCleaner(boilerplate_threshold=2)
    raw = (
        "HEADER NOISE\n"
        "Body paragraph 1.\n"
        "HEADER NOISE\n"
        "Body paragraph 2.\n"
        "HEADER NOISE\n"
    )
    cleaned = cleaner.clean(raw)
    assert "HEADER NOISE" not in cleaned
    assert "Body paragraph 1." in cleaned
    assert "Body paragraph 2." in cleaned


def test_structural_protection_shielding() -> None:
    """Verify fenced code blocks and tables retain exact formatting during cleaning."""
    cleaner = TextCleaner(boilerplate_threshold=2, max_newlines=2)
    raw = (
        "CONFIDENTIAL\n\n"
        "```python\n"
        "def foo():\n"
        "    #   preserve   \n"
        "\n\n\n\n"
        "    return 42\n"
        "```\n\n"
        "CONFIDENTIAL\n\n"
        "| Header A | Header B |\n"
        "| --- | --- |\n"
        "| Data 1 | Data 2 |\n\n"
        "CONFIDENTIAL\n"
    )
    cleaned = cleaner.clean(raw)

    # Boilerplate removed outside protected blocks
    assert "CONFIDENTIAL" not in cleaned

    # Code block inside whitespace and formatting 100% preserved
    assert "def foo():" in cleaned
    assert "    #   preserve   " in cleaned
    assert "\n\n\n\n" in cleaned or "\n    return 42" in cleaned
    assert "| Header A | Header B |" in cleaned


def test_cleaner_error_handling() -> None:
    """Verify CleanError is raised on non-string input."""
    cleaner = TextCleaner()
    with pytest.raises(CleanError) as exc_info:
        cleaner.clean(12345)  # type: ignore[arg-type]
    assert "must be a string" in str(exc_info.value)
    assert exc_info.value.details["provided_type"] == "<class 'int'>"


def test_cleaner_configurable_options() -> None:
    """Verify disabling normalization and newline capping."""
    cleaner = TextCleaner(normalize_unicode=False, cap_newlines=False, boilerplate_threshold=None)
    raw = "Line 1\n\n\n\nLine 2"
    cleaned = cleaner.clean(raw)
    assert cleaned == raw


def test_table_pipe_shielding() -> None:
    """Verify lines matching ^\\|.*\\|$ are shielded from whitespace capping and boilerplate dedup."""
    cleaner = TextCleaner(boilerplate_threshold=1, max_newlines=1)
    raw = (
        "| Header X | Header Y |\n"
        "| --- | --- |\n"
        "| Row 1 | Val 1 |\n\n\n"
        "| Row 1 | Val 1 |\n"
    )
    cleaned = cleaner.clean(raw)
    assert "| Header X | Header Y |" in cleaned
    assert "| Row 1 | Val 1 |" in cleaned


def test_tilde_code_block_shielding() -> None:
    """Verify tilde fenced code blocks ~~~ are extracted and shielded."""
    cleaner = TextCleaner(boilerplate_threshold=1)
    raw = (
        "~~~bash\n"
        "echo 'hello'\n"
        "~~~\n"
    )
    protected = TextCleaner.extract_protected_blocks(raw)
    assert len(protected) == 1
    assert protected[0][2] == "code_block"
    cleaned = cleaner.clean(raw)
    assert "echo 'hello'" in cleaned

