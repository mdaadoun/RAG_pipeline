# Session 7.3: Exit Code Gatekeeper
**Date:** 2026-08-09

Implemented Exit Code Gatekeeper in `src/ingestion/gatekeeper.py` (`ExitCodeGatekeeper`) and integrated it into `src/ingestion/cli.py`. Enforces CI/CD quality gates by evaluating `PipelineResult` metrics (character coverage ratio, orphan block count, document processing errors, audit status) and forcing non-zero exit code (`1`) when blocking alerts are present, breaking failing CI build runs.

---

### 1. 🎓 Concepts Introduced
- **Exit Code Gatekeeper:** Automated pipeline evaluation component that inspects aggregate and per-document audit metrics to issue exit code 0 (pass) or code 1 (fail) for CI/CD process control.
- **Quality Gate Policy:** Configurable rule set (e.g. minimum character coverage $\ge 0.98$, zero orphan blocks, zero document errors) required for data ingestion build approval.
- **Blocking Alert:** Critical data quality failure condition (e.g., fragmented Markdown tables or code blocks, parsing exceptions) that invalidates RAG corpus integrity and halts automated pipelines.

---

### 2. 🧠 Architecture Decisions (ADR)

#### [ADR-01: Decoupled Gatekeeper Component]
- **Option 1:** Embed inline boolean logic checks directly within `cli.py`.
- **Option 2 (Selected):** Implement `ExitCodeGatekeeper` in `src/ingestion/gatekeeper.py`. Adheres to domain/application layer separation, enabling independent unit testing of gate policy rules and reusability across non-CLI execution contexts.

#### [ADR-02: Comprehensive Indicator Aggregation]
- **Option 1:** Evaluate only `AuditReport.metrics.status`.
- **Option 2 (Selected):** Aggregate flags across `IngestionReport` (`has_blocking_alerts`, `documents_in_error`, `global_char_coverage_ratio`) and `AuditReport` (`metrics.status`). Prevents false negative CI passes by ensuring any single blocking alert triggers build failure.

#### [ADR-03: Detailed Failure Reason Extraction]
- **Option 1:** Print a generic exit code 1 error message.
- **Option 2 (Selected):** Implement `get_blocking_reasons()` on `ExitCodeGatekeeper` to collect human-readable bullet points detailing specific failure causes (e.g., orphan table counts, low coverage percentage, processing errors) prior to exiting.

---

### 3. 🛠️ Implementation & Code

```python
# src/ingestion/gatekeeper.py
class ExitCodeGatekeeper:
    """Evaluates pipeline ingestion reports to enforce CI/CD quality gate exit codes."""

    def __init__(self, coverage_threshold: float = 0.98) -> None:
        self.coverage_threshold = coverage_threshold

    def evaluate(self, result: PipelineResult) -> int:
        return 1 if self.should_exit(result) else 0

    def should_exit(self, result: PipelineResult) -> bool:
        ing_report = result.ingestion_report
        audit_report = result.audit_report
        return (
            ing_report.has_blocking_alerts
            or audit_report.metrics.status != "PASSED"
            or ing_report.documents_in_error > 0
            or ing_report.global_char_coverage_ratio < self.coverage_threshold
        )
```

```bash
# Verification suite execution
.venv/bin/pytest tests/unit/test_gatekeeper.py tests/unit/test_cli.py -v
# Result: 15 passed in 0.12s
```

---

### 4. 📌 Session Checklist & Deliverables
1. [x] **Exit Code Gatekeeper Module:** Implemented `ExitCodeGatekeeper` in `src/ingestion/gatekeeper.py` providing `evaluate()`, `should_exit()`, and `get_blocking_reasons()`.
2. [x] **CLI Command Integration:** Updated `src/ingestion/cli.py` to evaluate pipeline results using `ExitCodeGatekeeper` and print detailed blocking alert reasons before raising `typer.Exit(code=1)`.
3. [x] **Package Export:** Registered `ExitCodeGatekeeper` in `src/ingestion/__init__.py` `__all__` list.
4. [x] **Unit Testing:** Created `tests/unit/test_gatekeeper.py` and updated `tests/unit/test_cli.py` verifying exit code 1 on fixed chunking table splits and exit code 0 on recursive structural chunking.
5. [x] **Quality Assurance:** Verified 100% compliance with `mypy` strict typing, `ruff check`, and full pytest suite (131 passed).
