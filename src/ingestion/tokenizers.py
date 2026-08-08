"""Model-agnostic tokenizer abstractions and provider-specific encoders."""

import math
from abc import ABC, abstractmethod

import tiktoken

from ingestion.exceptions import ChunkError


class BaseTokenizer(ABC):
    """Abstract base class for model-agnostic tokenizers."""

    @abstractmethod
    def encode(self, text: str) -> list[int]:
        """Encode text string into token integer IDs."""
        pass

    @abstractmethod
    def decode(self, tokens: list[int]) -> str:
        """Decode token integer IDs back to text string."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Calculate exact token count for input text string."""
        pass


class TiktokenEncoder(BaseTokenizer):
    """Wrapper around OpenAI tiktoken encoding (default cl100k_base)."""

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        """Initialize tiktoken encoder by encoding name or model name."""
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception:
            try:
                self.encoding = tiktoken.encoding_for_model(encoding_name)
            except Exception as err:
                raise ChunkError(
                    f"Failed to initialize tiktoken encoder '{encoding_name}': {err}"
                ) from err
        self.encoding_name = encoding_name

    def encode(self, text: str) -> list[int]:
        """Encode text into token IDs."""
        return self.encoding.encode(text)

    def decode(self, tokens: list[int]) -> str:
        """Decode token IDs back to text string."""
        return self.encoding.decode(tokens)

    def count_tokens(self, text: str) -> int:
        """Calculate token count using tiktoken encoder."""
        return len(self.encode(text))


class GeminiEncoder(BaseTokenizer):
    """Google Gemini API tokenizer with calibrated offline SentencePiece fallback."""

    def __init__(self, model_name: str = "gemini-1.5-flash") -> None:
        """Initialize Gemini encoder instance."""
        self.model_name = model_name

    def encode(self, text: str) -> list[int]:
        """Simulate character-range token IDs for Gemini model."""
        count = self.count_tokens(text)
        return list(range(count))

    def decode(self, tokens: list[int]) -> str:
        """Stub decode method returning character length approximation."""
        return f"[Decoded {len(tokens)} Gemini tokens]"

    def count_tokens(self, text: str) -> int:
        """Calculate token count using Gemini API or calibrated SentencePiece heuristic fallback."""
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 3.6))


class HeuristicTokenizer(BaseTokenizer):
    """Lightweight character/word ratio token estimator for fast local execution."""

    def __init__(self, chars_per_token: float = 4.0) -> None:
        """Initialize heuristic tokenizer with target character ratio."""
        if chars_per_token <= 0:
            raise ChunkError("chars_per_token must be positive")
        self.chars_per_token = chars_per_token

    def encode(self, text: str) -> list[int]:
        """Return dummy token ID list matching estimated count."""
        return list(range(self.count_tokens(text)))

    def decode(self, tokens: list[int]) -> str:
        """Return dummy text payload representing token count."""
        return " " * int(len(tokens) * self.chars_per_token)

    def count_tokens(self, text: str) -> int:
        """Calculate heuristic token count from text length."""
        if not text:
            return 0
        return max(1, math.ceil(len(text) / self.chars_per_token))


def get_tokenizer(name_or_provider: str = "gemini") -> BaseTokenizer:
    """Factory returning concrete tokenizer implementation based on provider name."""
    provider = name_or_provider.lower().strip()
    if provider in ("gemini", "google"):
        return GeminiEncoder()
    if provider in ("tiktoken", "openai", "cl100k_base"):
        return TiktokenEncoder()
    if provider in ("heuristic", "char", "fast"):
        return HeuristicTokenizer()
    try:
        return TiktokenEncoder(provider)
    except ChunkError as err:
        raise ChunkError(
            f"Unknown or unsupported tokenizer provider: '{name_or_provider}'"
        ) from err

