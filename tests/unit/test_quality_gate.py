"""Unit tests for Quality Gates & Final Delivery verifier."""

import json
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from ingestion.quality_gate import QualityGateResult, QualityGateRunner


def test_quality_gate_result_model_immutability() -> None:
    """Verify QualityGateResult is frozen and rejects extra fields."""
    res = QualityGateResult(
        mypy_passed=True,
        ruff_passed=True,
        pytest_passed=True,
        coverage_passed=True,
        report_verified=True,
        all_passed=True,
        coverage_ratio=0.95,
        details=["OK"],
    )
    assert res.all_passed is True
    assert res.coverage_ratio == 0.95

    attr_name = "all_passed"
    with pytest.raises(ValidationError):
        setattr(res, attr_name, False)

    data: dict[str, object] = {
        "mypy_passed": True,
        "ruff_passed": True,
        "pytest_passed": True,
        "coverage_passed": True,
        "report_verified": True,
        "all_passed": True,
        "coverage_ratio": 0.95,
        "details": ["OK"],
        "extra_field": "invalid",
    }
    with pytest.raises(ValidationError):
        QualityGateResult.model_validate(data)


def test_verify_deliverable_schema(tmp_path: Path) -> None:
    """Verify schema validation for deliverable report file."""
    runner = QualityGateRunner(root_dir=tmp_path)

    # Missing file
    assert runner.verify_deliverable_schema("missing.json") is False

    # Corrupted JSON
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("invalid json", encoding="utf-8")
    assert runner.verify_deliverable_schema("bad.json") is False

    # Missing keys
    incomplete = tmp_path / "incomplete.json"
    incomplete.write_text(json.dumps({"timestamp": "123"}), encoding="utf-8")
    assert runner.verify_deliverable_schema("incomplete.json") is False

    # Valid deliverable
    valid = tmp_path / "rapport_ingestion.json"
    valid_data = {
        "timestamp": "2026-08-09T10:00:00Z",
        "strategy_used": "recursive",
        "metrics": {"status": "PASSED"},
        "document_ids": ["doc_1"],
    }
    valid.write_text(json.dumps(valid_data), encoding="utf-8")
    assert runner.verify_deliverable_schema("rapport_ingestion.json") is True


def test_quality_gate_runner_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify execution of code quality checks with mocked subprocesses."""
    runner = QualityGateRunner()

    dummy_proc = subprocess.CompletedProcess(
        args=["test"], returncode=0, stdout="PASSED", stderr=""
    )
    monkeypatch.setattr(
        subprocess, "run", lambda *args, **kwargs: dummy_proc
    )

    assert runner.run_typing_check() is True
    assert runner.run_lint_check() is True

    passed, cov = runner.run_test_suite()
    assert passed is True
    assert cov == 1.0

    report_file = tmp_path / "rapport_ingestion.json"
    report_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-08-09T10:00:00Z",
                "strategy_used": "recursive",
                "metrics": {"status": "PASSED"},
                "document_ids": ["doc_1"],
            }
        ),
        encoding="utf-8",
    )
    res = runner.evaluate_all(report_path=report_file)
    assert isinstance(res, QualityGateResult)
    assert res.all_passed is True
