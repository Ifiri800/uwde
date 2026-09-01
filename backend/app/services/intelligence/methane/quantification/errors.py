from __future__ import annotations


class QuantificationError(Exception):
    """Base exception for Layer 7 emissions quantification."""


class QuantificationValidationError(QuantificationError):
    """Raised when quantification input fails validation."""


class UnsupportedQuantificationMethodError(QuantificationError):
    """Raised when a quantification method is not supported."""


class UnsupportedQuantificationLevelError(QuantificationError):
    """Raised when a quantification level is not supported."""


class QuantificationCalculationError(QuantificationError):
    """Raised when an emissions calculation cannot be completed."""


class QuantificationRegistrationError(QuantificationError):
    """Raised when a quantifier cannot be registered or resolved."""
