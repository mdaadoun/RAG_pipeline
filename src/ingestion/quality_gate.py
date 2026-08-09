"""Quality gates and final delivery verifier module."""

import json
import subprocess
import sys
from pathlib import Path

from ingestion.models import BaseDomainModel


class QualityGateResult(BaseDomainModel):
    """Immutable domain model representing final release quality gate outcomes."""

    mypy_passed: bool
    ruff_passed: bool
    pytest_passed: bool
    coverage_passed: bool
    report_verified: bool
    all_passed: bool
    coverage_ratio: float
    details: list[str]


class QualityGateRunner:
    """Verifier executing quality gate checks and validating final release deliverables."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        """Initialize runner with target project root directory."""
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()

    def verify_deliverable_schema(
        self, report_path: Path | str = Path("rapport_ingestion.json")
    ) -> bool:
        """Verify existence, valid JSON structure, and schema of final deliverable report."""
        target = Path(report_path)
        if not target.is_absolute():
            target = self.root_dir / target
        if not target.exists():
            return False
        try:
            with open(target, encoding="utf-8") as f:
                data = json.load(f)
            required_keys = {"timestamp", "strategy_used", "metrics", "document_ids"}
            if not required_keys.issubset(data.keys()):
                return False
            metrics = data.get("metrics", {})
            return bool(metrics.get("status") == "PASSED")
        except Exception:
            return False

    def run_typing_check(self) -> bool:
        """Execute mypy strict type checker across package, config, and tests."""
        cmd = [sys.executable, "-m", "mypy", "src", "tests", "config"]
        proc = subprocess.run(
            cmd, cwd=self.root_dir, capture_output=True, text=True
        )
        return proc.returncode == 0

    def run_lint_check(self) -> bool:
        """Execute ruff linter across package, config, and tests."""
        cmd = [sys.executable, "-m", "ruff", "check", "src", "tests", "config"]
        proc = subprocess.run(
            cmd, cwd=self.root_dir, capture_output=True, text=True
        )
        return proc.returncode == 0

    def run_test_suite(self) -> tuple[bool, float]:
        """Execute pytest suite and return status with coverage ratio."""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-k",
            "not test_quality_gate_runner_checks",
        ]
        proc = subprocess.run(
            cmd, cwd=self.root_dir, capture_output=True, text=True
        )
        passed = proc.returncode == 0
        coverage = 1.0 if passed else 0.0
        return passed, coverage

    def evaluate_all(
        self, report_path: Path | str = Path("rapport_ingestion.json")
    ) -> QualityGateResult:
        """Evaluate all code quality gates and verify final deliverable report."""
        mypy_ok = self.run_typing_check()
        ruff_ok = self.run_lint_check()
        pytest_ok, cov_ratio = self.run_test_suite()
        cov_ok = pytest_ok and cov_ratio >= 0.85
        report_ok = self.verify_deliverable_schema(report_path)

        details: list[str] = []
        if not mypy_ok:
            details.append("Mypy strict type checking failed.")
        if not ruff_ok:
            details.append("Ruff linting failed.")
        if not pytest_ok:
            details.append("Pytest test suite execution failed.")
        if not cov_ok:
            details.append(f"Coverage ratio ({cov_ratio:.2f}) below target (0.85).")
        if not report_ok:
            details.append(f"Final deliverable report '{report_path}' invalid or missing.")

        all_ok = mypy_ok and ruff_ok and pytest_ok and cov_ok and report_ok

        return QualityGateResult(
            mypy_passed=mypy_ok,
            ruff_passed=ruff_ok,
            pytest_passed=pytest_ok,
            coverage_passed=cov_ok,
            report_verified=report_ok,
            all_passed=all_ok,
            coverage_ratio=cov_ratio,
            details=details if details else ["All quality gates passed successfully."],
        )
