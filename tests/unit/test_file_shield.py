"""Unit tests for file-level exception shielding."""

from pathlib import Path
from unittest.mock import patch

import pytest

from ingestion.file_shield import (
    FileShieldContext,
    IngestionStage,
    StageError,
)
from ingestion.models import DocumentReport, IngestionConfig
from ingestion.pipeline import PipelineOrchestrator

# --- IngestionStage Enum ---


def test_stage_enum_values() -> None:
    """Verify all pipeline stages are defined."""
    assert IngestionStage.LOAD.value == "load"
    assert IngestionStage.CLEAN.value == "clean"
    assert IngestionStage.CHUNK.value == "chunk"
    assert IngestionStage.AUDIT.value == "audit"


# --- StageError ---


def test_stage_error_frozen() -> None:
    """Verify StageError is immutable."""
    err = StageError(
        stage=IngestionStage.LOAD,
        error_type="ValueError",
        message="bad input",
        traceback="Traceback ...",
    )
    with pytest.raises(AttributeError):
        err.message = "changed"  # type: ignore[misc]


def test_stage_error_format_short() -> None:
    """Verify format_short produces concise error summary."""
    err = StageError(
        stage=IngestionStage.CLEAN,
        error_type="CleanError",
        message="unicode fail",
        traceback="tb...",
    )
    formatted = err.format_short()
    assert "[clean]" in formatted
    assert "CleanError" in formatted
    assert "unicode fail" in formatted


# --- FileShieldContext ---


def test_context_no_errors() -> None:
    """Verify fresh context has no errors."""
    ctx = FileShieldContext(file_path=Path("/tmp/test.md"))
    assert not ctx.has_errors
    assert ctx.failed_stages == []
    assert ctx.format_error_messages() == []
    assert ctx.format_tracebacks() == []


def test_context_record_error_captures_traceback() -> None:
    """Verify record_error captures exception traceback string."""
    ctx = FileShieldContext(file_path=Path("/tmp/test.md"))
    try:
        raise ValueError("test error message")
    except ValueError as exc:
        ctx.record_error(IngestionStage.LOAD, exc)

    assert ctx.has_errors
    assert len(ctx.errors) == 1
    assert ctx.errors[0].stage == IngestionStage.LOAD
    assert ctx.errors[0].error_type == "ValueError"
    assert ctx.errors[0].message == "test error message"
    assert "Traceback" in ctx.errors[0].traceback
    assert "ValueError" in ctx.errors[0].traceback


def test_context_multiple_errors() -> None:
    """Verify context accumulates errors from multiple stages."""
    ctx = FileShieldContext(file_path=Path("/tmp/test.md"))
    try:
        raise OSError("read failed")
    except OSError as exc:
        ctx.record_error(IngestionStage.LOAD, exc)
    try:
        raise RuntimeError("chunk exploded")
    except RuntimeError as exc:
        ctx.record_error(IngestionStage.CHUNK, exc)

    assert len(ctx.errors) == 2
    assert ctx.failed_stages == [IngestionStage.LOAD, IngestionStage.CHUNK]
    msgs = ctx.format_error_messages()
    assert len(msgs) == 2
    assert "[load]" in msgs[0]
    assert "[chunk]" in msgs[1]


def test_context_format_tracebacks() -> None:
    """Verify format_tracebacks returns full traceback strings."""
    ctx = FileShieldContext(file_path=Path("/tmp/test.md"))
    try:
        raise TypeError("bad type")
    except TypeError as exc:
        ctx.record_error(IngestionStage.CLEAN, exc)

    tbs = ctx.format_tracebacks()
    assert len(tbs) == 1
    assert "TypeError" in tbs[0]
    assert "bad type" in tbs[0]


# --- Pipeline Shield Integration ---


def test_shield_load_unsupported_format(tmp_path: Path) -> None:
    """Verify _shield_load records error for unsupported file type."""
    fake_file = tmp_path / "image.png"
    fake_file.write_bytes(b"\x89PNG")

    orch = PipelineOrchestrator()
    ctx = FileShieldContext(file_path=fake_file)
    result = orch._shield_load(fake_file, ctx)

    assert result is None
    assert ctx.has_errors
    assert ctx.errors[0].stage == IngestionStage.LOAD
    assert "Unsupported" in ctx.errors[0].message


def test_shield_read_missing_file(tmp_path: Path) -> None:
    """Verify _shield_read records error for missing file."""
    from ingestion.loaders import TextLoader

    fake_path = tmp_path / "missing.txt"
    loader = TextLoader(fake_path)

    orch = PipelineOrchestrator()
    ctx = FileShieldContext(file_path=fake_path)
    result = orch._shield_read(loader, fake_path, ctx)

    assert result is None
    assert ctx.has_errors
    assert ctx.errors[0].stage == IngestionStage.LOAD


def test_shield_clean_error(tmp_path: Path) -> None:
    """Verify _shield_clean records error on cleaner failure."""
    orch = PipelineOrchestrator()
    ctx = FileShieldContext(file_path=tmp_path / "test.md")

    with patch.object(
        orch._cleaner, "clean", side_effect=RuntimeError("clean boom"),
    ):
        result = orch._shield_clean("content", tmp_path / "test.md", ctx)

    assert result is None
    assert ctx.has_errors
    assert ctx.errors[0].stage == IngestionStage.CLEAN
    assert "clean boom" in ctx.errors[0].message


def test_shield_chunk_error(tmp_path: Path) -> None:
    """Verify _shield_chunk records error on chunker failure."""
    from ingestion.models import Document

    doc = Document(
        id="test_doc", file_path="test.md",
        content="Some content.", metadata={},
    )
    orch = PipelineOrchestrator()
    ctx = FileShieldContext(file_path=tmp_path / "test.md")

    with patch.object(
        orch._chunker, "chunk", side_effect=RuntimeError("chunk boom"),
    ):
        result = orch._shield_chunk(doc, tmp_path / "test.md", ctx)

    assert result is None
    assert ctx.has_errors
    assert ctx.errors[0].stage == IngestionStage.CHUNK
    assert "chunk boom" in ctx.errors[0].message


def test_shield_audit_error_returns_error_report(
    tmp_path: Path,
) -> None:
    """Verify _shield_audit returns error report on monitor failure."""
    from ingestion.models import Document

    doc = Document(
        id="test_doc", file_path=str(tmp_path / "test.md"),
        content="Some content.", metadata={},
    )
    orch = PipelineOrchestrator()
    ctx = FileShieldContext(file_path=tmp_path / "test.md")

    with patch.object(
        orch._monitor, "audit_document",
        side_effect=RuntimeError("audit boom"),
    ):
        report = orch._shield_audit(doc, [], ctx)

    assert isinstance(report, DocumentReport)
    assert report.status == "error"
    assert any("audit boom" in e for e in report.errors)


# --- End-to-End Shielding ---


def test_batch_continues_after_file_error(tmp_path: Path) -> None:
    """Verify batch run continues processing after one file fails."""
    (tmp_path / "good.md").write_text("# Good Doc\n\nValid content.")
    (tmp_path / "image.png").write_bytes(b"\x89PNG")

    orch = PipelineOrchestrator(IngestionConfig(chunk_size=200))
    result = orch.run(
        input_dir=tmp_path,
        output_dir=tmp_path / "out",
        report_path=tmp_path / "rpt.json",
    )

    assert len(result.documents) == 1
    error_reports = [r for r in result.doc_reports if r.status == "error"]
    assert len(error_reports) >= 1
    assert any("[load]" in e for r in error_reports for e in r.errors)


def test_traceback_preserved_in_error_report(tmp_path: Path) -> None:
    """Verify traceback info propagates to DocumentReport errors."""
    ctx = FileShieldContext(file_path=Path("/test/file.md"))
    try:
        raise ValueError("detailed failure")
    except ValueError as exc:
        ctx.record_error(IngestionStage.LOAD, exc)

    orch = PipelineOrchestrator()
    report = orch._error_report(Path("/test/file.md"), ctx)
    assert report.status == "error"
    assert any("ValueError" in e for e in report.errors)
    # Full tracebacks available through context
    tbs = ctx.format_tracebacks()
    assert len(tbs) == 1
    assert "Traceback" in tbs[0]
