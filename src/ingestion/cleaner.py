"""Text cleaner with NFKC normalization and structure preservation."""

import re
import unicodedata


class TextCleaner:
    """Document text cleaning and normalization utility."""

    def __init__(self, normalize_unicode: bool = True) -> None:
        self.normalize_unicode = normalize_unicode

    def clean(self, text: str) -> str:
        """Clean and normalize raw document text."""
        cleaned = text
        if self.normalize_unicode:
            cleaned = unicodedata.normalize("NFKC", cleaned)
        # Remove null bytes & non-printable control characters (except newline/tab)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)
        return cleaned

    @staticmethod
    def extract_protected_blocks(text: str) -> list[tuple[int, int, str]]:
        """Identify line boundaries of Markdown tables and code blocks."""
        protected: list[tuple[int, int, str]] = []
        # Match fenced code blocks ```...```
        for match in re.finditer(r"```[\s\S]*?```", text):
            protected.append((match.start(), match.end(), "code_block"))
        # Match Markdown table blocks (|...|)
        table_pattern = r"(?:(?:^|\n)\|[^\n]+\|\n\|[-:| ]+\|\n(?:\|[^\n]+\|\n?)+)"
        for match in re.finditer(table_pattern, text):
            protected.append((match.start(), match.end(), "table"))
        return protected
