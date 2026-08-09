"""File-level exception shielding for per-stage ingestion errors."""

import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TypeVar

from config.logging import get_logger

logger = get_logger("file_shield")

T = TypeVar("T")


class IngestionStage(str, Enum):
    """Named ingestion pipeline processing stages."""

    LOAD = "load"
    CLEAN = "clean"
    CHUNK = "chunk"
    AUDIT = "audit"


@dataclass(frozen=True)
class StageError:
    """Captured error from a single processing stage."""

    stage: IngestionStage
    error_type: str
    message: str
    traceback: str

    def format_short(self) -> str:
        """Format concise single-line error summary."""
        return f"[{self.stage.value}] {self.error_type}: {self.message}"


@dataclass
class FileShieldContext:
    """Accumulates per-stage errors for a single file."""

    file_path: Path
    errors: list[StageError] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if any stage recorded an error."""
        return len(self.errors) > 0

    @property
    def failed_stages(self) -> list[IngestionStage]:
        """Return list of stages that failed."""
        return [e.stage for e in self.errors]

    def record_error(
        self,
        stage: IngestionStage,
        exc: BaseException,
    ) -> None:
        """Capture exception with traceback for a given stage."""
        tb_str = traceback.format_exception(
            type(exc), exc, exc.__traceback__,
        )
        error = StageError(
            stage=stage,
            error_type=type(exc).__name__,
            message=str(exc),
            traceback="".join(tb_str),
        )
        self.errors.append(error)
        logger.warning(
            "stage_error",
            file=str(self.file_path),
            stage=stage.value,
            error=error.format_short(),
        )

    def format_error_messages(self) -> list[str]:
        """Format all errors as short strings for DocumentReport.errors."""
        return [e.format_short() for e in self.errors]

    def format_tracebacks(self) -> list[str]:
        """Return full traceback strings for diagnostics."""
        return [e.traceback for e in self.errors]


def shield_stage(
    stage: IngestionStage,
    func: Callable[[], T],
    ctx: FileShieldContext,
) -> T | None:
    """Execute function safely within stage context recording any exceptions."""
    try:
        return func()
    except Exception as exc:
        ctx.record_error(stage, exc)
        return None
