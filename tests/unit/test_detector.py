"""Unit tests for OrphanBlockDetector scanner and boundary evaluation."""

from ingestion.detector import OrphanBlockDetector
from ingestion.models import Chunk


def test_extract_structural_blocks() -> None:
    """Verify extraction of tables, code blocks, and math blocks with exact offsets."""
    text = (
        "# Title\n\n"
        "```python\nprint('hello')\n```\n\n"
        "| Col1 | Col2 |\n| --- | --- |\n| A | B |\n\n"
        "$$\nx^2 + y^2 = z^2\n$$"
    )
    detector = OrphanBlockDetector()
    blocks = detector.extract_structural_blocks(text)
    assert len(blocks) == 3
    types = [b.block_type for b in blocks]
    assert "code_block" in types
    assert "table" in types
    assert "math_block" in types


def test_orphan_block_detector_table_split() -> None:
    """Verify table split across chunk boundaries returns orphan_count > 0."""
    text = (
        "Intro text\n"
        "| Name | Age |\n"
        "| --- | --- |\n"
        "| Alice | 30 |\n"
        "| Bob | 25 |\n"
        "Outro text"
    )
    split_idx = text.find("| Bob")
    c1 = Chunk(
        id="c1",
        doc_id="d1",
        chunk_index=0,
        content=text[:split_idx],
        start_char=0,
        end_char=split_idx,
        token_count=10,
    )
    c2 = Chunk(
        id="c2",
        doc_id="d1",
        chunk_index=1,
        content=text[split_idx:],
        start_char=split_idx,
        end_char=len(text),
        token_count=10,
    )

    detector = OrphanBlockDetector()
    orphan_count = detector.detect_orphan_blocks(text, [c1, c2])
    assert orphan_count == 1


def test_orphan_block_detector_table_intact() -> None:
    """Verify table fully contained in single chunk returns orphan_count == 0."""
    text = (
        "| Name | Age |\n"
        "| --- | --- |\n"
        "| Alice | 30 |"
    )
    c1 = Chunk(
        id="c1",
        doc_id="d1",
        chunk_index=0,
        content=text,
        start_char=0,
        end_char=len(text),
        token_count=10,
    )
    detector = OrphanBlockDetector()
    assert detector.detect_orphan_blocks(text, [c1]) == 0


def test_orphan_block_detector_code_block_split() -> None:
    """Verify fenced code block split across chunks is flagged as orphan block."""
    text = "Intro\n```python\ndef foo():\n    return 'bar'\n```\nOutro"
    split_idx = text.find("return")
    c1 = Chunk(
        id="c1",
        doc_id="d2",
        chunk_index=0,
        content=text[:split_idx],
        start_char=0,
        end_char=split_idx,
        token_count=8,
    )
    c2 = Chunk(
        id="c2",
        doc_id="d2",
        chunk_index=1,
        content=text[split_idx:],
        start_char=split_idx,
        end_char=len(text),
        token_count=8,
    )
    detector = OrphanBlockDetector()
    assert detector.detect_orphan_blocks(text, [c1, c2]) == 1


def test_is_orphan_chunk() -> None:
    """Verify is_orphan_chunk identifies chunks containing severed structural blocks."""
    text = "| Col1 | Col2 |\n| --- | --- |\n| Val1 | Val2 |"
    split_idx = text.find("| Val1")
    c1 = Chunk(
        id="c1",
        doc_id="d3",
        chunk_index=0,
        content=text[:split_idx],
        start_char=0,
        end_char=split_idx,
        token_count=5,
    )
    c_intact = Chunk(
        id="c_full",
        doc_id="d3",
        chunk_index=0,
        content=text,
        start_char=0,
        end_char=len(text),
        token_count=10,
    )

    detector = OrphanBlockDetector()
    assert detector.is_orphan_chunk(c1, text) is True
    assert detector.is_orphan_chunk(c_intact, text) is False


def test_orphan_detector_empty_and_edge_cases() -> None:
    """Verify detector handles empty text or empty chunk lists gracefully."""
    detector = OrphanBlockDetector()
    assert detector.detect_orphan_blocks("", []) == 0
    assert detector.detect_orphan_blocks("Some text", []) == 0

    chunk = Chunk(
        id="c0",
        doc_id="d0",
        chunk_index=0,
        content="test",
        start_char=0,
        end_char=4,
        token_count=1,
        is_orphan_block=True,
    )
    assert detector.is_orphan_chunk(chunk, "") is True
