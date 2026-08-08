"""Document loading abstractions and standard format loaders."""

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from ingestion.models import Document


class DocumentLoader(ABC):
    """Abstract base class for document loaders."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    @abstractmethod
    def load(self) -> Document:
        """Load source file and return typed Document domain model."""
        pass


class TextLoader(DocumentLoader):
    """Loader for standard plain text files."""

    def load(self) -> Document:
        """Load text file from disk."""
        content = self.file_path.read_text(encoding="utf-8")
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        return Document(
            id=doc_id,
            file_path=str(self.file_path),
            content=content,
            metadata={"format": "txt", "filename": self.file_path.name},
        )


class MarkdownLoader(DocumentLoader):
    """Loader for Markdown documents with structural headers."""

    def load(self) -> Document:
        """Load markdown file from disk."""
        content = self.file_path.read_text(encoding="utf-8")
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        return Document(
            id=doc_id,
            file_path=str(self.file_path),
            content=content,
            metadata={"format": "markdown", "filename": self.file_path.name},
        )
