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
    """

    category: FailureCategory
    retryable: bool
    reason: str
    error_type: str
    status_code: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "retryable": self.retryable,
            "reason": self.reason,
            "error_type": self.error_type,
            "status_code": self.status_code,
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

    The classifier deliberately uses conservative rules:
    known transient failures are retryable, while known
    permanent failures are not.
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
    )
