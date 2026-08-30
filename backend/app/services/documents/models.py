from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DocumentType(StrEnum):
    """Supported uploaded document and data formats."""

    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"
    TXT = "txt"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"


class DocumentSource(StrEnum):
    """Origin of an acquired document."""

    UPLOAD = "upload"


@dataclass(frozen=True)
class DocumentMetadata:
    """Metadata describing an acquired document."""

    filename: str
    media_type: str
    document_type: DocumentType
    size_bytes: int
    source: DocumentSource = DocumentSource.UPLOAD

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError("filename is required")

        if not self.media_type.strip():
            raise ValueError("media_type is required")

        if self.size_bytes < 0:
            raise ValueError("size_bytes cannot be negative")


@dataclass
class DocumentAcquisitionResult:
    """
    Common result produced by document acquisition.

    Structured documents may populate `records`.
    Text-oriented documents may populate `text`.
    """

    metadata: DocumentMetadata
    records: list[dict[str, Any]] = field(default_factory=list)
    text: str | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def record_count(self) -> int:
        """Return the number of structured records acquired."""
        return len(self.records)

    @property
    def has_records(self) -> bool:
        """Return True when structured records were acquired."""
        return bool(self.records)

    @property
    def has_text(self) -> bool:
        """Return True when document text was acquired."""
        return bool(self.text)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the acquisition result."""
        return {
            "metadata": {
                "filename": self.metadata.filename,
                "media_type": self.metadata.media_type,
                "document_type": self.metadata.document_type.value,
                "size_bytes": self.metadata.size_bytes,
                "source": self.metadata.source.value,
            },
            "record_count": self.record_count,
            "records": self.records,
            "text": self.text,
            "raw_metadata": self.raw_metadata,
        }
