"""Unit tests for text cleaner and normalization layer."""

from ingestion.cleaner import TextCleaner


def test_cleaner_nfkc_normalization() -> None:
    """Verify NFKC normalization strips null bytes and cleans text."""
    cleaner = TextCleaner()
    raw = "Hello\x00 World! NFKC test."
    cleaned = cleaner.clean(raw)
    assert "\x00" not in cleaned
    assert "Hello World!" in cleaned


def test_extract_protected_blocks() -> None:
    """Verify code block and table extraction indices."""
    text = "Header\n\n```python\nprint('hello')\n```\n"
    protected = TextCleaner.extract_protected_blocks(text)
    assert len(protected) == 1
    assert protected[0][2] == "code_block"
