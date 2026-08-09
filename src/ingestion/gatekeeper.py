"""Exit code gatekeeper enforcing quality gates for pipeline execution."""

from ingestion.models import IngestionReport
from ingestion.pipeline import PipelineResult


class ExitCodeGatekeeper:
    """Evaluates pipeline ingestion reports to enforce CI/CD quality gate exit codes."""

    def __init__(self, coverage_threshold: float = 0.98) -> None:
        """Initialize gatekeeper with minimum coverage threshold."""
        self.coverage_threshold = coverage_threshold

    def evaluate(self, result: PipelineResult) -> int:
        """Return exit code 0 if all quality gates pass, 1 if blocking alerts exist."""
        return 1 if self.should_exit(result) else 0

    def should_exit(self, result: PipelineResult) -> bool:
        """Check if pipeline result contains any blocking quality alerts."""
        ing_report: IngestionReport = result.ingestion_report
        audit_report = result.audit_report

        if ing_report.has_blocking_alerts:
            return True
        if audit_report.metrics.status != "PASSED":
            return True
        if ing_report.documents_in_error > 0:
            return True
        if ing_report.global_char_coverage_ratio < self.coverage_threshold:
            return True
        return False

    def get_blocking_reasons(self, result: PipelineResult) -> list[str]:
        """Collect human-readable explanation list for all triggered blocking alerts."""
        reasons: list[str] = []
        ing_report: IngestionReport = result.ingestion_report
        audit_report = result.audit_report

        if ing_report.documents_in_error > 0:
            reasons.append(
                f"Processing errors encountered in {ing_report.documents_in_error} document(s)"
            )

        orphan_count = sum(d.orphan_blocks for d in ing_report.documents)
        if orphan_count > 0:
            reasons.append(
                f"Detected {orphan_count} orphaned Markdown table or code block(s)"
            )

        if ing_report.global_char_coverage_ratio < self.coverage_threshold:
            reasons.append(
                f"Global character coverage ratio ({ing_report.global_char_coverage_ratio:.4f}) "
                f"is below threshold ({self.coverage_threshold:.4f})"
            )

        if audit_report.metrics.status != "PASSED":
            reasons.append(
                f"Audit metric status evaluated to '{audit_report.metrics.status}'"
            )

        if not reasons and ing_report.has_blocking_alerts:
            reasons.append("Generic blocking alert flag set on ingestion report")

        return reasons
