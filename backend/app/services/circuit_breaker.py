from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import Lock
from time import monotonic
from typing import Any, Callable, TypeVar


T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Raised when a circuit blocks an operation."""

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
    Thread-safe circuit breaker.

    CLOSED:
        Normal execution.

    OPEN:
        Execution is blocked until the recovery timeout.

    HALF_OPEN:
        Exactly one probe is permitted at a time.
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
        with self._lock:
            self._close()

    def snapshot(self) -> CircuitBreakerSnapshot:
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


class CircuitBreakerRegistry:
    """
    Thread-safe registry of persistent circuit breakers.

    A circuit is keyed by a stable target name, allowing failures
    from separate pipeline executions to contribute to the same
    circuit.
    """

    def __init__(
        self,
        config: CircuitBreakerConfig | None = None,
    ) -> None:
        self.config = config or CircuitBreakerConfig()
        self._circuits: dict[str, CircuitBreaker] = {}
        self._lock = Lock()

    def get(self, name: str) -> CircuitBreaker:
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "circuit name must not be empty"
            )

        with self._lock:
            circuit = self._circuits.get(
                normalized_name
            )

            if circuit is None:
                circuit = CircuitBreaker(
                    normalized_name,
                    self.config,
                )
                self._circuits[normalized_name] = circuit

            return circuit

    def reset(self, name: str) -> None:
        with self._lock:
            circuit = self._circuits.get(
                name.strip()
            )

            if circuit is not None:
                circuit.reset()

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {
                name: circuit.to_dict()
                for name, circuit in self._circuits.items()
            }

    def clear(self) -> None:
        with self._lock:
            self._circuits.clear()


_GLOBAL_CIRCUIT_REGISTRY = CircuitBreakerRegistry()


def get_circuit_breaker(
    name: str,
) -> CircuitBreaker:
    """
    Return the persistent process-level circuit for a target.
    """
    return _GLOBAL_CIRCUIT_REGISTRY.get(name)


def get_circuit_registry() -> CircuitBreakerRegistry:
    """
    Return the process-level circuit registry.
    """
    return _GLOBAL_CIRCUIT_REGISTRY
