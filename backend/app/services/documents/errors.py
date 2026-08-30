from __future__ import annotations


class DocumentAcquisitionError(Exception):
    """Base exception for document acquisition failures."""


class UnsupportedDocumentType(DocumentAcquisitionError):
    """Raised when the uploaded file type is not supported."""


class InvalidDocument(DocumentAcquisitionError):
    """Raised when the uploaded document is malformed or invalid."""


class DocumentTooLarge(DocumentAcquisitionError):
    """Raised when the document exceeds the configured size limit."""


class DocumentParseError(DocumentAcquisitionError):
    """Raised when a supported document cannot be parsed."""
