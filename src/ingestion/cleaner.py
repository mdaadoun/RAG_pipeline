"""Text cleaner module with NFKC normalization, whitespace capping, and structural shielding."""

import re
import unicodedata
import uuid

from ingestion.exceptions import CleanError


class TextCleaner:
    """Document text cleaning, normalization, and protection engine."""

    def __init__(
        self,
        normalize_unicode: bool = True,
        remove_control_chars: bool = True,
        cap_newlines: bool = True,
        max_newlines: int = 2,
        boilerplate_threshold: int | None = 3,
        shield_protected: bool = True,
    ) -> None:
        self.normalize_unicode = normalize_unicode
        self.remove_control_chars = remove_control_chars
        self.cap_newlines = cap_newlines
        self.max_newlines = max_newlines
        self.boilerplate_threshold = boilerplate_threshold
        self.shield_protected = shield_protected

    def clean(self, text: str, boilerplate_threshold: int | None = None) -> str:
        """Clean and normalize raw document text while preserving protected blocks."""
        if not isinstance(text, str):
            raise CleanError(
                "Input text must be a string",
                details={"provided_type": str(type(text))},
            )

        if not text:
            return ""

        try:
            effective_threshold = (
                boilerplate_threshold
                if boilerplate_threshold is not None
                else self.boilerplate_threshold
            )
            placeholders: dict[str, str] = {}
            processed = text

            if self.shield_protected:
                processed, placeholders = self._shield_protected_blocks(processed)

            if self.normalize_unicode:
                processed = unicodedata.normalize("NFKC", processed)

            if self.remove_control_chars:
                processed = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", processed)

            # Standardize non-breaking spaces and line trailing whitespace
            processed = processed.replace("\xa0", " ")
            lines = [line.rstrip() for line in processed.split("\n")]
            processed = "\n".join(lines)

            if effective_threshold is not None and effective_threshold > 0:
                processed = self._deduplicate_boilerplate(processed, effective_threshold)

            if self.cap_newlines and self.max_newlines >= 0:
                pattern = r"\n{" + str(self.max_newlines + 1) + r",}"
                replacement = "\n" * self.max_newlines
                processed = re.sub(pattern, replacement, processed)

            if self.shield_protected and placeholders:
                processed = self._unshield_protected_blocks(processed, placeholders)

            return processed
        except CleanError:
            raise
        except Exception as err:
            raise CleanError(
                f"Unexpected failure during text cleaning: {err}",
                details={"error": str(err)},
            ) from err

    @staticmethod
    def extract_protected_blocks(text: str) -> list[tuple[int, int, str]]:
        """Identify line boundaries of Markdown tables and code blocks."""
        protected: list[tuple[int, int, str]] = []
        # Code blocks fenced by ``` or ~~~
        for match in re.finditer(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)", text):
            protected.append((match.start(), match.end(), "code_block"))

        # Markdown tables matching lines starting with | and ending with | (^\|.*\|$)
        table_pattern = r"(?:^|\n)([ \t]*\|.*\|[ \t]*(?:\n[ \t]*\|.*\|[ \t]*)*)"
        for match in re.finditer(table_pattern, text):
            start = match.start(1)
            end = match.end(1)
            if not any(
                (p_start <= start < p_end) or (p_start < end <= p_end) or (start <= p_start and end >= p_end)
                for p_start, p_end, _ in protected
            ):
                protected.append((start, end, "table"))

        protected.sort(key=lambda item: item[0])
        return protected

    def _shield_protected_blocks(self, text: str) -> tuple[str, dict[str, str]]:
        """Replace protected blocks with unique placeholder tokens."""
        protected_regions = self.extract_protected_blocks(text)
        if not protected_regions:
            return text, {}

        placeholders: dict[str, str] = {}
        token_prefix = f"___SHIELDED_{uuid.uuid4().hex[:8]}_"
        result_parts: list[str] = []
        last_idx = 0

        for idx, (start, end, _block_type) in enumerate(protected_regions):
            if start < last_idx:
                continue
            token = f"{token_prefix}{idx}___"
            result_parts.append(text[last_idx:start])
            result_parts.append(token)
            placeholders[token] = text[start:end]
            last_idx = end

        result_parts.append(text[last_idx:])
        return "".join(result_parts), placeholders

    def _unshield_protected_blocks(self, text: str, placeholders: dict[str, str]) -> str:
        """Restore original text for protected placeholders."""
        result = text
        for token, original_content in placeholders.items():
            result = result.replace(token, original_content)
        return result

    def _deduplicate_boilerplate(self, text: str, threshold: int) -> str:
        """Remove non-empty lines repeating more than threshold occurrences."""
        lines = text.split("\n")
        counts: dict[str, int] = {}
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("___SHIELDED_"):
                counts[stripped] = counts.get(stripped, 0) + 1

        filtered_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("___SHIELDED_") and counts.get(stripped, 0) > threshold:
                continue
            filtered_lines.append(line)

        return "\n".join(filtered_lines)

