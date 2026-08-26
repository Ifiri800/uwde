from __future__ import annotations

from dataclasses import dataclass
from threading import Condition, Lock
from time import monotonic
from typing import Any, Callable, TypeVar


T = TypeVar("T")


class BulkheadRejectedError(RuntimeError):
    """Raised when a bulkhead cannot accept another operation."""

    def __init__(self, name: str) -> None:
        self.name = name

        super().__init__(
            f"Bulkhead '{name}' rejected the operation "
            "because capacity is unavailable."
        )


@dataclass(frozen=True)
class BulkheadConfig:
    """Configuration for a bulkhead isolation boundary."""

    max_concurrency: int = 5
    max_queue_size: int = 10
    acquisition_timeout_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.max_concurrency < 1:
            raise ValueError(
                "max_concurrency must be at least 1"
            )

        if self.max_queue_size < 0:
            raise ValueError(
                "max_queue_size must be non-negative"
            )

        if self.acquisition_timeout_seconds < 0:
            raise ValueError(
                "acquisition_timeout_seconds must be non-negative"
            )


@dataclass
class BulkheadSnapshot:
    """Serializable snapshot of bulkhead state."""

    name: str
    max_concurrency: int
    max_queue_size: int
    acquisition_timeout_seconds: float
    active: int
    queued: int
    available: int
    total_accepted: int
    total_rejected: int
    total_completed: int
    total_failed: int

    @property
    def utilization(self) -> float:
        return (
            self.active / self.max_concurrency
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "max_concurrency": self.max_concurrency,
            "max_queue_size": self.max_queue_size,
            "acquisition_timeout_seconds": (
                self.acquisition_timeout_seconds
            ),
            "active": self.active,
            "queued": self.queued,
            "available": self.available,
            "total_accepted": self.total_accepted,
            "total_rejected": self.total_rejected,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "utilization": self.utilization,
        }


class Bulkhead:
    """
    Thread-safe concurrency isolation boundary.

    Only a bounded number of operations may execute at the
    same time. Additional operations may wait within the
    configured queue capacity.
    """

    def __init__(
        self,
        name: str,
        config: BulkheadConfig | None = None,
    ) -> None:
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "bulkhead name must not be empty"
            )

        self.name = normalized_name
        self.config = config or BulkheadConfig()

        self._condition = Condition(Lock())

        self._active = 0
        self._queued = 0

        self._total_accepted = 0
        self._total_rejected = 0
        self._total_completed = 0
        self._total_failed = 0

    @property
    def active(self) -> int:
        with self._condition:
            return self._active

    @property
    def queued(self) -> int:
        with self._condition:
            return self._queued

    @property
    def available(self) -> int:
        with self._condition:
            return max(
                0,
                self.config.max_concurrency
                - self._active,
            )

    def acquire(self) -> None:
        deadline = (
            monotonic()
            + self.config.acquisition_timeout_seconds
        )

        with self._condition:
            if self._active < self.config.max_concurrency:
                self._active += 1
                self._total_accepted += 1
                return

            if self._queued >= self.config.max_queue_size:
                self._total_rejected += 1
                raise BulkheadRejectedError(self.name)

            self._queued += 1

            try:
                while self._active >= self.config.max_concurrency:
                    remaining = deadline - monotonic()

                    if remaining <= 0:
                        self._total_rejected += 1
                        raise BulkheadRejectedError(
                            self.name
                        )

                    self._condition.wait(
                        timeout=remaining
                    )

                self._active += 1
                self._total_accepted += 1

            finally:
                self._queued -= 1

    def release(self) -> None:
        with self._condition:
            if self._active <= 0:
                raise RuntimeError(
                    "Bulkhead release called without "
                    "a matching acquire"
                )

            self._active -= 1
            self._total_completed += 1

            self._condition.notify()

    def record_failure(self) -> None:
        with self._condition:
            self._total_failed += 1

    def execute(
        self,
        operation: Callable[[], T],
    ) -> T:
        self.acquire()

        try:
            result = operation()
        except Exception:
            self.record_failure()
            self.release()
            raise

        self.release()

        return result

    def snapshot(self) -> BulkheadSnapshot:
        with self._condition:
            return BulkheadSnapshot(
                name=self.name,
                max_concurrency=(
                    self.config.max_concurrency
                ),
                max_queue_size=(
                    self.config.max_queue_size
                ),
                acquisition_timeout_seconds=(
                    self.config.acquisition_timeout_seconds
                ),
                active=self._active,
                queued=self._queued,
                available=max(
                    0,
                    self.config.max_concurrency
                    - self._active,
                ),
                total_accepted=(
                    self._total_accepted
                ),
                total_rejected=(
                    self._total_rejected
                ),
                total_completed=(
                    self._total_completed
                ),
                total_failed=self._total_failed,
            )

    def to_dict(self) -> dict[str, Any]:
        return self.snapshot().to_dict()
