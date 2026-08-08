"""Unit tests for model-agnostic tokenizers and provider encoders."""

import pytest

from ingestion.exceptions import ChunkError
from ingestion.tokenizers import (
    BaseTokenizer,
    GeminiEncoder,
    HeuristicTokenizer,
    TiktokenEncoder,
    get_tokenizer,
)


def test_base_tokenizer_abc_instantiation() -> None:
    """Verify BaseTokenizer ABC cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseTokenizer()  # type: ignore[abstract]


def test_tiktoken_encoder() -> None:
    """Verify TiktokenEncoder encoding, decoding, and counting."""
    encoder = TiktokenEncoder("cl100k_base")
    text = "RAG ingestion pipeline with Gemini and Tiktoken."
    tokens = encoder.encode(text)
    assert len(tokens) > 0
    assert encoder.decode(tokens) == text
    assert encoder.count_tokens(text) == len(tokens)


def test_gemini_encoder() -> None:
    """Verify GeminiEncoder count_tokens and fallback handling."""
    encoder = GeminiEncoder("gemini-1.5-flash")
    text = "Ce document est un test de tokenisation pour Gemini."
    tokens = encoder.encode(text)
    assert len(tokens) > 0
    assert encoder.count_tokens(text) == len(tokens)
    assert encoder.count_tokens("") == 0
    assert "[Decoded" in encoder.decode(tokens)


def test_heuristic_tokenizer() -> None:
    """Verify HeuristicTokenizer ratio estimation and bounds validation."""
    with pytest.raises(ChunkError, match="chars_per_token must be positive"):
        HeuristicTokenizer(chars_per_token=0)

    tokenizer = HeuristicTokenizer(chars_per_token=4.0)
    text = "123456789012"  # 12 chars -> 3 tokens
    assert tokenizer.count_tokens(text) == 3
    assert tokenizer.count_tokens("") == 0


def test_get_tokenizer_factory() -> None:
    """Verify get_tokenizer factory routes correctly by provider name."""
    gemini = get_tokenizer("gemini")
    tiktoken_enc = get_tokenizer("tiktoken")
    heuristic = get_tokenizer("heuristic")

    assert isinstance(gemini, GeminiEncoder)
    assert isinstance(tiktoken_enc, TiktokenEncoder)
    assert isinstance(heuristic, HeuristicTokenizer)

    with pytest.raises(ChunkError, match="Unknown or unsupported tokenizer provider"):
        get_tokenizer("invalid_provider_xyz")
