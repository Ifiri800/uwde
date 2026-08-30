from __future__ import annotations

from pathlib import Path

from .errors import UnsupportedDocumentType
from .models import DocumentType


_EXTENSION_MAP: dict[str, DocumentType] = {
    ".csv": DocumentType.CSV,
    ".xlsx": DocumentType.XLSX,
    ".json": DocumentType.JSON,
    ".txt": DocumentType.TXT,
    ".html": DocumentType.HTML,
    ".htm": DocumentType.HTML,
    ".pdf": DocumentType.PDF,
    ".docx": DocumentType.DOCX,
}


_MEDIA_TYPE_MAP: dict[str, DocumentType] = {
    "text/csv": DocumentType.CSV,
    "application/csv": DocumentType.CSV,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": DocumentType.XLSX,
    "application/json": DocumentType.JSON,
    "text/plain": DocumentType.TXT,
    "text/html": DocumentType.HTML,
    "application/pdf": DocumentType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.DOCX,
}


def detect_document_type(
    filename: str,
    media_type: str | None = None,
) -> DocumentType:
    """
    Determine the supported document type from filename and media type.

    The filename extension is the primary signal. When no supported
    extension is available, the supplied media type is used.
    """

    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("filename is required")

    normalized_filename = filename.strip().lower()
    extension = Path(normalized_filename).suffix

    if extension in _EXTENSION_MAP:
        return _EXTENSION_MAP[extension]

    if media_type:
        normalized_media_type = media_type.split(";", 1)[0].strip().lower()

        if normalized_media_type in _MEDIA_TYPE_MAP:
            return _MEDIA_TYPE_MAP[normalized_media_type]

    raise UnsupportedDocumentType(
        f"Unsupported document type for filename: {filename!r}"
    )


def supported_extensions() -> tuple[str, ...]:
    """Return all supported file extensions."""
    return tuple(sorted(_EXTENSION_MAP))


def supported_document_types() -> tuple[DocumentType, ...]:
    """Return all supported document types."""
    return tuple(DocumentType)
