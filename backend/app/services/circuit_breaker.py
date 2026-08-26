from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import Lock
from time import monotonic
from typing import Any, Callable, TypeVar


T = TypeVar("T")


class CircuitState(str, Enum):
    """Possible states of a circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Raised when execution is blocked by an open circuit."""

    def __init__(
        self,
        name: str,
        state: CircuitState,
    ) -> None:
        self.name = name
        self.state = state

        super().__init__(
            f"Circuit '{name}' is {state.value}; "
            "execution is temporarily blocked."
        )


@dataclass(frozen=True)
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout_seconds: float = 30.0
    success_threshold: int = 1

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError(
                "failure_threshold must be at least 1"
            )

        if self.recovery_timeout_seconds < 0:
            raise ValueError(
                "recovery_timeout_seconds must be non-negative"
            )

        if self.success_threshold < 1:
            raise ValueError(
                "success_threshold must be at least 1"
            )


@dataclass
class CircuitBreakerSnapshot:
    """Serializable circuit breaker state."""

    name: str
    state: CircuitState
    consecutive_failures: int
    consecutive_successes: int
    total_successes: int
    total_failures: int
    opened_at: float | None
    last_failure_at: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "opened_at": self.opened_at,
            "last_failure_at": self.last_failure_at,
        }


class CircuitBreaker:
    """
    Thread-safe circuit breaker for protecting unreliable operations.

    CLOSED:
        Operations execute normally.

    OPEN:
        Operations are blocked until the recovery timeout expires.

    HALF_OPEN:
        A limited probe is allowed to determine whether the
        protected operation has recovered.
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> None:
        if not name.strip():
            raise ValueError("name must not be empty")

        self.name = name
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._total_successes = 0
        self._total_failures = 0
        self._opened_at: float | None = None
        self._last_failure_at: float | None = None

        self._half_open_probe_in_flight = False

        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._refresh_state()

            return self._state

    def allow_request(self) -> bool:
        """
        Determine whether a protected operation may execute.

        CLOSED:
            allow.

        OPEN:
            block until recovery timeout has elapsed.

        HALF_OPEN:
            allow exactly one probe at a time.
        """
        with self._lock:
            self._refresh_state()

            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                return False

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_probe_in_flight:
                    return False

                self._half_open_probe_in_flight = True

                return True

            return False

    def record_success(self) -> None:
        """Record a successful protected operation."""
        with self._lock:
            self._total_successes += 1

            if self._state == CircuitState.HALF_OPEN:
                self._consecutive_successes += 1
                self._half_open_probe_in_flight = False

                if (
                    self._consecutive_successes
                    >= self.config.success_threshold
                ):
                    self._close()

                return

            self._consecutive_successes += 1
            self._consecutive_failures = 0

    def record_failure(self) -> None:
        """Record a failed protected operation."""
        with self._lock:
            self._total_failures += 1
            self._last_failure_at = monotonic()
            self._consecutive_successes = 0

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_probe_in_flight = False
                self._open()
                return

            if self._state == CircuitState.CLOSED:
                self._consecutive_failures += 1

                if (
                    self._consecutive_failures
                    >= self.config.failure_threshold
                ):
                    self._open()

    def call(
        self,
        operation: Callable[[], T],
    ) -> T:
        """
        Execute an operation through the circuit breaker.

        CircuitOpenError is raised when execution is blocked.
        """
        if not self.allow_request():
            raise CircuitOpenError(
                self.name,
                self.state,
            )

        try:
            result = operation()
        except Exception:
            self.record_failure()
            raise
        else:
            self.record_success()
            return result

    def reset(self) -> None:
        """Manually reset the circuit to CLOSED."""
        with self._lock:
            self._close()

    def snapshot(self) -> CircuitBreakerSnapshot:
        """Return a serializable snapshot of current state."""
        with self._lock:
            self._refresh_state()

            return CircuitBreakerSnapshot(
                name=self.name,
                state=self._state,
                consecutive_failures=(
                    self._consecutive_failures
                ),
                consecutive_successes=(
                    self._consecutive_successes
                ),
                total_successes=self._total_successes,
                total_failures=self._total_failures,
                opened_at=self._opened_at,
                last_failure_at=self._last_failure_at,
            )

    def to_dict(self) -> dict[str, Any]:
        """Return the current state as a dictionary."""
        return self.snapshot().to_dict()

    def _refresh_state(self) -> None:
        if self._state != CircuitState.OPEN:
            return

        if self._opened_at is None:
            return

        elapsed = monotonic() - self._opened_at

        if (
            elapsed
            >= self.config.recovery_timeout_seconds
        ):
            self._state = CircuitState.HALF_OPEN
            self._consecutive_successes = 0
            self._half_open_probe_in_flight = False

    def _open(self) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = monotonic()
        self._consecutive_successes = 0
        self._half_open_probe_in_flight = False

    def _close(self) -> None:
        self._state = CircuitState.CLOSED
        self._opened_at = None
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._half_open_probe_in_flight = False
