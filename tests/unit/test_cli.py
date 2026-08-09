"""Unit tests for Typer CLI commands and options in ingestion/cli.py."""

from pathlib import Path

from typer.testing import CliRunner

from ingestion.cli import app

runner = CliRunner()


def test_cli_help() -> None:
    """Verify CLI --help option lists command options and descriptions."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--input" in result.output
    assert "--output" in result.output
    assert "--strategy" in result.output
    assert "--chunk-size" in result.output
    assert "--overlap" in result.output
    assert "--min-chunk-size" in result.output
    assert "--report" in result.output


def test_cli_run_success(fixtures_dir: Path, tmp_path: Path) -> None:
    """Verify successful CLI run with default options on fixture directory."""
    output_dir = tmp_path / "output"
    report_file = tmp_path / "report.json"

    result = runner.invoke(
        app,
        [
            "--input",
            str(fixtures_dir),
            "--output",
            str(output_dir),
            "--report",
            str(report_file),
            "--strategy",
            "recursive",
        ],
    )

    assert result.exit_code == 0
    assert "Ingestion Pipeline Launch" in result.output
    assert "Ingestion Audit Results" in result.output
    assert (output_dir / "chunks.jsonl").exists()
    assert report_file.exists()


def test_cli_run_custom_parameters(fixtures_dir: Path, tmp_path: Path) -> None:
    """Verify CLI execution with explicit strategy and chunking options."""
    output_dir = tmp_path / "custom_out"
    report_file = tmp_path / "custom_report.json"

    result = runner.invoke(
        app,
        [
            "-i",
            str(fixtures_dir),
            "-o",
            str(output_dir),
            "-r",
            str(report_file),
            "-s",
            "recursive",
            "-c",
            "256",
            "--overlap",
            "32",
            "--min-chunk-size",
            "20",
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "chunks.jsonl").exists()
    assert report_file.exists()


def test_cli_invalid_strategy(fixtures_dir: Path, tmp_path: Path) -> None:
    """Verify CLI exits with code 1 when given invalid chunking strategy."""
    result = runner.invoke(
        app,
        [
            "--input",
            str(fixtures_dir),
            "--strategy",
            "invalid_strategy_xyz",
        ],
    )

    assert result.exit_code == 1
    assert "Ingestion Error" in result.output


def test_cli_empty_directory(tmp_path: Path) -> None:
    """Verify CLI handles empty input directory cleanly."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    output_dir = tmp_path / "out"
    report_file = tmp_path / "rep.json"

    result = runner.invoke(
        app,
        [
            "--input",
            str(empty_dir),
            "--output",
            str(output_dir),
            "--report",
            str(report_file),
        ],
    )

    assert result.exit_code == 0
    assert "Total Input Docs" in result.output


def test_cli_gatekeeper_exit_code_1_on_fixed_strategy_table_split(
    fixtures_dir: Path, tmp_path: Path
) -> None:
    """Verify CLI gatekeeper exits with code 1 when fixed chunking splits table blocks."""
    output_dir = tmp_path / "out_fixed"
    report_file = tmp_path / "report_fixed.json"

    result = runner.invoke(
        app,
        [
            "--input",
            str(fixtures_dir),
            "--output",
            str(output_dir),
            "--report",
            str(report_file),
            "--strategy",
            "fixed",
            "--chunk-size",
            "60",
            "--overlap",
            "10",
        ],
    )

    assert result.exit_code == 1
    assert "CRITICAL: Quality gates failed!" in result.output
    assert "Detected" in result.output or "Audit metric status" in result.output


def test_cli_gatekeeper_exit_code_0_on_recursive_strategy(
    fixtures_dir: Path, tmp_path: Path
) -> None:
    """Verify CLI gatekeeper exits with code 0 on recursive structural chunking."""
    output_dir = tmp_path / "out_rec"
    report_file = tmp_path / "report_rec.json"

    result = runner.invoke(
        app,
        [
            "--input",
            str(fixtures_dir),
            "--output",
            str(output_dir),
            "--report",
            str(report_file),
            "--strategy",
            "recursive",
            "--chunk-size",
            "512",
        ],
    )

    assert result.exit_code == 0

