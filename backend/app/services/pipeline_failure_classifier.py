from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FailureCategory(str, Enum):
    """
    Classification of pipeline failures.

    TRANSIENT failures may succeed if retried.
    PERMANENT failures should not normally be retried.
    UNKNOWN failures use the configured fallback policy.
    """

    TRANSIENT = "transient"
    PERMANENT = "permanent"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FailureClassification:
    """
    Structured classification of an exception.

    The classification provides both retry policy information
    and an explicit recovery recommendation for the reliability
    subsystem.
    """

    category: FailureCategory
    retryable: bool
    reason: str
    error_type: str
    status_code: int | None = None
    recovery_action: str | None = None
    recovery_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "retryable": self.retryable,
            "reason": self.reason,
            "error_type": self.error_type,
            "status_code": self.status_code,
            "recovery_action": self.recovery_action,
            "recovery_reason": self.recovery_reason,
        }


_TRANSIENT_STATUS_CODES = {
    408,
    425,
    429,
    500,
    502,
    503,
    504,
}

_PERMANENT_STATUS_CODES = {
    400,
    401,
    403,
    404,
    405,
    406,
    409,
    410,
    411,
    412,
    413,
    415,
    422,
    423,
    424,
    426,
    428,
}


def classify_failure(
    error: Exception,
) -> FailureClassification:
    """
    Classify a pipeline exception as transient, permanent,
    or unknown.

    Known transient failures are retryable.
    Known permanent failures are not retryable.
    Unknown failures remain non-retryable.
    """

    error_type = error.__class__.__name__
    message = str(error).strip()

    status_code = getattr(error, "status_code", None)

    if isinstance(status_code, int):
        if status_code in _TRANSIENT_STATUS_CODES:
            return FailureClassification(
                category=FailureCategory.TRANSIENT,
                retryable=True,
                reason=(
                    f"HTTP {status_code} indicates a "
                    "potentially temporary failure"
                ),
                error_type=error_type,
                status_code=status_code,
                recovery_action="retry",
                recovery_reason=(
                    "Retry the operation because the HTTP "
                    "status indicates a potentially temporary failure."
                ),
            )

        if status_code in _PERMANENT_STATUS_CODES:
            return FailureClassification(
                category=FailureCategory.PERMANENT,
                retryable=False,
                reason=(
                    f"HTTP {status_code} indicates a "
                    "non-retryable request failure"
                ),
                error_type=error_type,
                status_code=status_code,
                recovery_action="abort",
                recovery_reason=(
                    "Do not retry because the HTTP status "
                    "indicates a non-retryable request failure."
                ),
            )

    transient_exception_names = {
        "TimeoutError",
        "ConnectionError",
        "ConnectionResetError",
        "BrokenPipeError",
    }

    if error_type in transient_exception_names:
        return FailureClassification(
            category=FailureCategory.TRANSIENT,
            retryable=True,
            reason=(
                f"{error_type} may be resolved by retrying"
            ),
            error_type=error_type,
            status_code=status_code,
            recovery_action="retry",
            recovery_reason=(
                f"{error_type} may be temporary and the "
                "operation should be retried."
            ),
        )

    transient_terms = (
        "timeout",
        "timed out",
        "temporarily unavailable",
        "temporary failure",
        "connection reset",
        "connection refused",
        "service unavailable",
        "rate limit",
        "too many requests",
    )

    lowered_message = message.lower()

    if any(
        term in lowered_message
        for term in transient_terms
    ):
        return FailureClassification(
            category=FailureCategory.TRANSIENT,
            retryable=True,
            reason=(
                "Error message indicates a temporary "
                "or recoverable failure"
            ),
            error_type=error_type,
            status_code=status_code,
            recovery_action="retry",
            recovery_reason=(
                "The error message indicates a temporary "
                "or recoverable condition."
            ),
        )

    # Generic runtime failures may represent temporary failures
    # during extraction. Keep them retryable as a controlled
    # compatibility policy.
    if isinstance(error, RuntimeError):
        return FailureClassification(
            category=FailureCategory.TRANSIENT,
            retryable=True,
            reason=(
                "RuntimeError may represent a temporary "
                "execution failure and is eligible for controlled retry"
            ),
            error_type=error_type,
            status_code=status_code,
            recovery_action="retry",
            recovery_reason=(
                "RuntimeError may represent a temporary "
                "execution failure and is eligible for controlled retry."
            ),
        )

    return FailureClassification(
        category=FailureCategory.UNKNOWN,
        retryable=False,
        reason=(
            "Failure type is not explicitly classified "
            "as retryable"
        ),
        error_type=error_type,
        status_code=status_code,
        recovery_action="abort",
        recovery_reason=(
            "The failure is not explicitly classified as retryable."
        ),
    )
