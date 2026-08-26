from __future__ import annotations

from backend.app.services.pipeline_failure_classifier import (
    FailureCategory,
    classify_failure,
)


class HTTPError(Exception):
    def __init__(
        self,
        status_code: int,
        message: str = "",
    ) -> None:
        super().__init__(message or f"HTTP {status_code}")
        self.status_code = status_code


def test_timeout_is_transient():
    result = classify_failure(
        TimeoutError("request timed out")
    )

    assert result.category == FailureCategory.TRANSIENT
    assert result.retryable is True


def test_connection_error_is_transient():
    result = classify_failure(
        ConnectionError("connection reset")
    )

    assert result.category == FailureCategory.TRANSIENT
    assert result.retryable is True


def test_http_429_is_transient():
    result = classify_failure(
        HTTPError(429)
    )

    assert result.category == FailureCategory.TRANSIENT
    assert result.retryable is True
    assert result.status_code == 429


def test_http_503_is_transient():
    result = classify_failure(
        HTTPError(503)
    )

    assert result.category == FailureCategory.TRANSIENT
    assert result.retryable is True


def test_http_404_is_permanent():
    result = classify_failure(
        HTTPError(404)
    )

    assert result.category == FailureCategory.PERMANENT
    assert result.retryable is False


def test_http_403_is_permanent():
    result = classify_failure(
        HTTPError(403)
    )

    assert result.category == FailureCategory.PERMANENT
    assert result.retryable is False


def test_unknown_error_is_not_retried():
    result = classify_failure(
        ValueError("invalid extraction configuration")
    )

    assert result.category == FailureCategory.UNKNOWN
    assert result.retryable is False


def test_serialization_contains_classification():
    result = classify_failure(
        TimeoutError("timeout")
    )

    data = result.to_dict()

    assert data["category"] == "transient"
    assert data["retryable"] is True
    assert data["error_type"] == "TimeoutError"
