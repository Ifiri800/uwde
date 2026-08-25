from __future__ import annotations

import json

import pytest

from backend.app.services.pipeline_reliability import (
    PipelineReliabilityTracker,
    RetryPolicy,
)


def test_retry_policy_defaults():
    policy = RetryPolicy()

    assert policy.max_attempts == 3
    assert policy.initial_delay_seconds == 0.5
    assert policy.max_delay_seconds == 10.0
    assert policy.backoff_multiplier == 2.0


def test_retry_policy_calculates_exponential_backoff():
    policy = RetryPolicy(
        max_attempts=4,
        initial_delay_seconds=1.0,
        max_delay_seconds=10.0,
        backoff_multiplier=2.0,
    )

    assert policy.delay_for_attempt(1) == 1.0
    assert policy.delay_for_attempt(2) == 2.0
    assert policy.delay_for_attempt(3) == 4.0
    assert policy.delay_for_attempt(4) == 8.0


def test_retry_policy_respects_maximum_delay():
    policy = RetryPolicy(
        max_attempts=5,
        initial_delay_seconds=2.0,
        max_delay_seconds=5.0,
        backoff_multiplier=3.0,
    )

    assert policy.delay_for_attempt(1) == 2.0
    assert policy.delay_for_attempt(2) == 5.0
    assert policy.delay_for_attempt(3) == 5.0


def test_retry_policy_rejects_invalid_values():
    with pytest.raises(
        ValueError,
        match="max_attempts must be at least 1",
    ):
        RetryPolicy(max_attempts=0)

    with pytest.raises(
        ValueError,
        match="initial_delay_seconds must be non-negative",
    ):
        RetryPolicy(initial_delay_seconds=-1)

    with pytest.raises(
        ValueError,
        match="max_delay_seconds must be non-negative",
    ):
        RetryPolicy(max_delay_seconds=-1)

    with pytest.raises(
        ValueError,
        match="backoff_multiplier must be at least 1",
    ):
        RetryPolicy(backoff_multiplier=0.5)


def test_retry_policy_rejects_invalid_attempt():
    policy = RetryPolicy()

    with pytest.raises(
        ValueError,
        match="attempt must be at least 1",
    ):
        policy.delay_for_attempt(0)


def test_tracker_creates_reliability_metadata():
    tracker = PipelineReliabilityTracker()

    metadata = tracker.metadata

    assert metadata.reliability_id
    assert metadata.started_at
    assert metadata.completed_at is None
    assert metadata.duration_ms is None
    assert metadata.status == "running"
    assert metadata.retry_count == 0
    assert metadata.recovered is False
    assert metadata.attempt_count == 0


def test_tracker_records_successful_attempt():
    tracker = PipelineReliabilityTracker()

    attempt = tracker.start_attempt()

    assert attempt.attempt == 1
    assert attempt.status == "running"
    assert attempt.started_at

    tracker.complete_attempt(attempt)

    assert attempt.status == "success"
    assert attempt.completed_at
    assert attempt.duration_ms is not None
    assert attempt.duration_ms >= 0


def test_tracker_records_failed_attempt():
    tracker = PipelineReliabilityTracker()

    attempt = tracker.start_attempt()

    error = RuntimeError("Temporary network failure")

    tracker.fail_attempt(
        attempt,
        error,
    )

    assert attempt.status == "failed"
    assert attempt.completed_at
    assert attempt.duration_ms is not None
    assert attempt.duration_ms >= 0
    assert attempt.error == (
        "Temporary network failure"
    )
    assert attempt.error_type == "RuntimeError"


def test_tracker_allows_retry_after_failure():
    tracker = PipelineReliabilityTracker(
        RetryPolicy(max_attempts=3)
    )

    first_attempt = tracker.start_attempt()

    tracker.fail_attempt(
        first_attempt,
        RuntimeError("Temporary failure"),
    )

    assert tracker.can_retry() is True
    assert tracker.metadata.retry_count == 0

    second_attempt = tracker.start_attempt()

    assert second_attempt.attempt == 2

    tracker.fail_attempt(
        second_attempt,
        RuntimeError("Temporary failure"),
    )

    assert tracker.can_retry() is True
    assert tracker.metadata.retry_count == 1

    third_attempt = tracker.start_attempt()

    assert third_attempt.attempt == 3


def test_tracker_prevents_attempt_after_maximum():
    tracker = PipelineReliabilityTracker(
        RetryPolicy(max_attempts=2)
    )

    first_attempt = tracker.start_attempt()

    tracker.fail_attempt(
        first_attempt,
        RuntimeError("Failure 1"),
    )

    second_attempt = tracker.start_attempt()

    tracker.fail_attempt(
        second_attempt,
        RuntimeError("Failure 2"),
    )

    assert tracker.can_retry() is False

    with pytest.raises(
        RuntimeError,
        match="Maximum retry attempts exceeded",
    ):
        tracker.start_attempt()


def test_tracker_calculates_next_retry_delay():
    tracker = PipelineReliabilityTracker(
        RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=1.0,
            backoff_multiplier=2.0,
        )
    )

    assert tracker.next_retry_delay() == 1.0

    attempt = tracker.start_attempt()

    tracker.fail_attempt(
        attempt,
        RuntimeError("Temporary failure"),
    )

    assert tracker.next_retry_delay() == 2.0

    attempt = tracker.start_attempt()

    tracker.fail_attempt(
        attempt,
        RuntimeError("Temporary failure"),
    )

    assert tracker.next_retry_delay() == 4.0


def test_tracker_completes_successfully_without_retry():
    tracker = PipelineReliabilityTracker()

    attempt = tracker.start_attempt()

    tracker.complete_attempt(attempt)

    metadata = tracker.complete()

    assert metadata.status == "success"
    assert metadata.completed_at
    assert metadata.duration_ms is not None
    assert metadata.duration_ms >= 0
    assert metadata.recovered is False
    assert metadata.retry_count == 0
    assert metadata.attempt_count == 1


def test_tracker_records_recovered_operation():
    tracker = PipelineReliabilityTracker(
        RetryPolicy(max_attempts=3)
    )

    first_attempt = tracker.start_attempt()

    tracker.fail_attempt(
        first_attempt,
        RuntimeError("Temporary failure"),
    )

    second_attempt = tracker.start_attempt()

    tracker.complete_attempt(second_attempt)

    metadata = tracker.complete(
        recovered=True,
    )

    assert metadata.status == "success"
    assert metadata.recovered is True
    assert metadata.attempt_count == 2
    assert metadata.retry_count == 1
    assert metadata.completed_at
    assert metadata.duration_ms is not None


def test_tracker_records_final_failure():
    tracker = PipelineReliabilityTracker(
        RetryPolicy(max_attempts=1)
    )

    attempt = tracker.start_attempt()

    error = RuntimeError(
        "Permanent extraction failure"
    )

    tracker.fail_attempt(
        attempt,
        error,
    )

    metadata = tracker.fail(error)

    assert metadata.status == "failed"
    assert metadata.completed_at
    assert metadata.duration_ms is not None
    assert metadata.final_error == (
        "Permanent extraction failure"
    )
    assert metadata.final_error_type == (
        "RuntimeError"
    )


def test_tracker_metadata_is_serializable():
    tracker = PipelineReliabilityTracker()

    attempt = tracker.start_attempt()

    tracker.complete_attempt(attempt)

    metadata = tracker.complete()

    serialized = metadata.to_dict()

    json.dumps(serialized)

    assert serialized["reliability_id"]
    assert serialized["started_at"]
    assert serialized["completed_at"]
    assert serialized["duration_ms"] is not None
    assert serialized["status"] == "success"
    assert serialized["attempt_count"] == 1
    assert serialized["retry_count"] == 0
    assert serialized["recovered"] is False
    assert len(serialized["attempts"]) == 1


def test_tracker_to_dict_matches_metadata():
    tracker = PipelineReliabilityTracker()

    attempt = tracker.start_attempt()

    tracker.complete_attempt(attempt)

    tracker.complete()

    result = tracker.to_dict()

    assert result["reliability_id"] == (
        tracker.metadata.reliability_id
    )

    assert result["status"] == "success"
    assert result["attempt_count"] == 1