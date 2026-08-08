"""Document loading abstractions and standard format loaders."""

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path

from ingestion.exceptions import DocumentLoadError
from ingestion.models import LoadedDocument


def compute_document_id(file_name: str, content: str) -> str:
    """Compute deterministic SHA-256 document identifier."""
    digest = hashlib.sha256(f"{file_name}:{content}".encode()).hexdigest()[:12]
    return f"doc_{digest}"


class DocumentLoader(ABC):
    """Abstract base class for document loaders."""

    def __init__(self, file_path: str | Path | None = None) -> None:
        self.file_path = Path(file_path) if file_path else None

    def _resolve_path(self, file_path: str | Path | None = None) -> Path:
        """Resolve and validate target file path."""
        target = Path(file_path) if file_path else self.file_path
        if target is None:
            raise DocumentLoadError("No file path provided to loader.")
        if not target.exists() or not target.is_file():
            raise DocumentLoadError(
                f"Source file not found: {target}",
                details={"file_path": str(target)},
            )
        return target

    def _read_content(self, path: Path) -> str:
        """Read text content with UTF-8 decoding and error wrapping."""
        try:
            return path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            raise DocumentLoadError(
                f"Failed to read file '{path}': {exc}",
                details={"file_path": str(path), "error": str(exc)},
            ) from exc

    @abstractmethod
    def load(self, file_path: str | Path | None = None) -> LoadedDocument:
        """Load target source file and return typed domain model."""
        pass


class TextLoader(DocumentLoader):
    """Loader for standard plain text files."""

    def load(self, file_path: str | Path | None = None) -> LoadedDocument:
        """Load text file from disk."""
        target = self._resolve_path(file_path)
        content = self._read_content(target)
        doc_id = compute_document_id(target.name, content)
        return LoadedDocument(
            id=doc_id,
            file_path=str(target),
            content=content,
            metadata={
                "format": "txt",
                "filename": target.name,
                "file_size_bytes": target.stat().st_size,
            },
        )


class MarkdownLoader(DocumentLoader):
    """Loader for Markdown documents."""

    def load(self, file_path: str | Path | None = None) -> LoadedDocument:
        """Load markdown file from disk."""
        target = self._resolve_path(file_path)
        content = self._read_content(target)
        doc_id = compute_document_id(target.name, content)
        return LoadedDocument(
            id=doc_id,
            file_path=str(target),
            content=content,
            metadata={
                "format": "markdown",
                "filename": target.name,
                "file_size_bytes": target.stat().st_size,
            },
        )


class TextMarkdownLoader(DocumentLoader):
    """Unified loader for plaintext and markdown documents."""

    def load(self, file_path: str | Path | None = None) -> LoadedDocument:
        """Load document auto-detecting text or markdown format."""
        target = self._resolve_path(file_path)
        ext = target.suffix.lower()
        fmt = "markdown" if ext in (".md", ".markdown") else "txt"
        content = self._read_content(target)
        doc_id = compute_document_id(target.name, content)
        return LoadedDocument(
            id=doc_id,
            file_path=str(target),
            content=content,
            metadata={
                "format": fmt,
                "filename": target.name,
                "file_size_bytes": target.stat().st_size,
            },
        )


def get_loader(file_path: str | Path) -> DocumentLoader:
    """Factory returning appropriate loader for given file extension."""
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext in (".md", ".markdown"):
        return MarkdownLoader(path)
    if ext in (".txt", ".text"):
        return TextLoader(path)
    raise DocumentLoadError(
        f"Unsupported file format: '{ext}' for file {path}",
        details={"file_path": str(path), "extension": ext},
    )

