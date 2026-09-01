from __future__ import annotations


class QualityError(Exception):
    """Base exception for Layer 6 quality operations."""


class QualityValidationError(QualityError):
    """Raised when a quality input violates required rules."""


class QualityAssessmentError(QualityError):
    """Raised when a quality assessment cannot be completed."""


class QualityEvidenceError(QualityError):
    """Raised when evidence requirements are violated."""


class QualityAuditError(QualityError):
    """Raised when an audit-trail operation fails."""


class QualityCalibrationError(QualityError):
    """Raised when calibration validation fails."""
