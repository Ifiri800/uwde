```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class RetryPolicy:
    """
    Defines retry behaviour for a pipeline operation.
    """

    max_attempts: int = 3
    initial_delay_seconds: float = 0.5
    max_delay_seconds: float = 10.0
    backoff_multiplier: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError(
                "max_attempts must be at least 1"
            )

        if self.initial_delay_seconds < 0:
            raise ValueError(
                "initial_delay_seconds must be non-negative"
            )

        if self.max_delay_seconds < 0:
            raise ValueError(
                "max_delay_seconds must be non-negative"
            )

        if self.backoff_multiplier < 1:
            raise ValueError(
                "backoff_multiplier must be at least 1"
            )

    def delay_for_attempt(
        self,
        attempt: int,
    ) -> float:
        """
        Return the delay before the supplied retry attempt.
        """

        if attempt < 1:
            raise ValueError(
                "attempt must be at least 1"
            )

        delay = (
            self.initial_delay_seconds
            * (
                self.backoff_multiplier
                ** (attempt - 1)
            )
        )

        return min(
            delay,
            self.max_delay_seconds,
        )


@dataclass
class ReliabilityAttempt:
    """
    Records one execution attempt.
    """

    attempt: int
    started_at: str
    completed_at: str | None = None
    duration_ms: float | None = None
    status: str = "running"
    error: str | None = None
    error_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
            "error_type": self.error_type,
        }


@dataclass
class PipelineReliabilityMetadata:
    """
    Reliability metadata for one pipeline operation.
    """

    reliability_id: str
    started_at: str
    completed_at: str | None = None
    duration_ms: float | None = None
    status: str = "running"
    attempts: list[ReliabilityAttempt] = field(
        default_factory=list
    )
    retry_count: int = 0
    recovered: bool = False
    final_error: str | None = None
    final_error_type: str | None = None

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reliability_id": self.reliability_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attempt_count": self.attempt_count,
            "retry_count": self.retry_count,
            "recovered": self.recovered,
            "final_error": self.final_error,
            "final_error_type": self.final_error_type,
            "attempts": [
                attempt.to_dict()
                for attempt in self.attempts
            ],
        }


class PipelineReliabilityTracker:
    """
    Tracks retry and recovery behaviour for one
    pipeline operation.

    Attempt 1 is the original execution.

    Every attempt after attempt 1 is a retry.

    Therefore:

        1 attempt -> retry_count = 0
        2 attempts -> retry_count = 1
        3 attempts -> retry_count = 2
    """

    def __init__(
        self,
        policy: RetryPolicy | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)

        self.policy = policy or RetryPolicy()
        self._started = now

        self.metadata = PipelineReliabilityMetadata(
            reliability_id=str(uuid4()),
            started_at=now.isoformat(),
        )

    def start_attempt(self) -> ReliabilityAttempt:
        """
        Start and register a new execution attempt.
        """

        if self.metadata.status in {
            "completed",
            "success",
            "failed",
        }:
            raise RuntimeError(
                "Reliability tracking has already completed"
            )

        attempt_number = (
            len(self.metadata.attempts) + 1
        )

        if attempt_number > self.policy.max_attempts:
            raise RuntimeError(
                "Maximum retry attempts exceeded"
            )

        now = datetime.now(timezone.utc)

        attempt = ReliabilityAttempt(
            attempt=attempt_number,
            started_at=now.isoformat(),
        )

        self.metadata.attempts.append(attempt)

        # The first attempt is the original operation.
        # Every subsequent attempt is a retry.
        self.metadata.retry_count = (
            attempt_number - 1
        )

        return attempt

    def complete_attempt(
        self,
        attempt: ReliabilityAttempt,
    ) -> None:
        """
        Mark an attempt as successful.
        """

        now = datetime.now(timezone.utc)

        attempt.status = "success"
        attempt.completed_at = now.isoformat()

        started = datetime.fromisoformat(
            attempt.started_at
        )

        attempt.duration_ms = (
            now - started
        ).total_seconds() * 1000

    def fail_attempt(
        self,
        attempt: ReliabilityAttempt,
        error: Exception | str,
    ) -> None:
        """
        Mark an attempt as failed.

        A failed first attempt does not count as a retry.
        A retry is counted when the next attempt starts.
        """

        now = datetime.now(timezone.utc)

        attempt.status = "failed"
        attempt.completed_at = now.isoformat()
        attempt.error = str(error)

        if isinstance(error, Exception):
            attempt.error_type = (
                error.__class__.__name__
            )
        else:
            attempt.error_type = "Exception"

        started = datetime.fromisoformat(
            attempt.started_at
        )

        attempt.duration_ms = (
            now - started
        ).total_seconds() * 1000

        # Keep metadata synchronized with the attempts
        # already registered.
        self.metadata.retry_count = max(
            0,
            len(self.metadata.attempts) - 1,
        )

    def complete(
        self,
        recovered: bool = False,
    ) -> PipelineReliabilityMetadata:
        """
        Mark the operation as successfully completed.
        """

        now = datetime.now(timezone.utc)

        self.metadata.completed_at = now.isoformat()

        self.metadata.duration_ms = (
            now - self._started
        ).total_seconds() * 1000

        self.metadata.status = "success"
        self.metadata.recovered = recovered

        # Final consistency check.
        self.metadata.retry_count = max(
            0,
            len(self.metadata.attempts) - 1,
        )

        return self.metadata

    def fail(
        self,
        error: Exception | str,
    ) -> PipelineReliabilityMetadata:
        """
        Mark the operation as permanently failed.
        """

        now = datetime.now(timezone.utc)

        self.metadata.completed_at = now.isoformat()

        self.metadata.duration_ms = (
            now - self._started
        ).total_seconds() * 1000

        self.metadata.status = "failed"
        self.metadata.final_error = str(error)

        if isinstance(error, Exception):
            self.metadata.final_error_type = (
                error.__class__.__name__
            )
        else:
            self.metadata.final_error_type = "Exception"

        self.metadata.retry_count = max(
            0,
            len(self.metadata.attempts) - 1,
        )

        return self.metadata

    def can_retry(self) -> bool:
        """
        Return whether another attempt is permitted.
        """

        return (
            len(self.metadata.attempts)
            < self.policy.max_attempts
        )

    def next_retry_delay(self) -> float:
        """
        Calculate the delay for the next attempt.
        """

        next_attempt = (
            len(self.metadata.attempts) + 1
        )

        if next_attempt > self.policy.max_attempts:
            return 0.0

        return self.policy.delay_for_attempt(
            next_attempt
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize reliability metadata.
        """

        return self.metadata.to_dict()
```
