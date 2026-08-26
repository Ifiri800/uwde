from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.services.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
)

from backend.app.services.pipeline_failure_classifier import (
    FailureClassification,
)

from backend.app.services.pipeline_reliability import (
    RetryPolicy,
)


class ResilienceAction(str, Enum):
    """Action selected by the adaptive resilience engine."""

    RETRY = "retry"
    WAIT = "wait"
    STOP = "stop"


@dataclass(frozen=True)
class AdaptiveResilienceConfig:
    """Configuration for adaptive failure-pressure handling."""

    max_adaptive_delay_seconds: float = 60.0
    failure_pressure_threshold: int = 3

    def __post_init__(self) -> None:
        if self.max_adaptive_delay_seconds < 0:
            raise ValueError(
                "max_adaptive_delay_seconds must be non-negative"
            )

        if self.failure_pressure_threshold < 1:
            raise ValueError(
                "failure_pressure_threshold must be at least 1"
            )


@dataclass(frozen=True)
class AdaptiveResilienceDecision:
    """Serializable resilience decision for one failed operation."""

    action: ResilienceAction
    delay_seconds: float
    retryable: bool
    circuit_state: CircuitState
    attempt: int
    consecutive_failures: int
    failure_category: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "delay_seconds": self.delay_seconds,
            "retryable": self.retryable,
            "circuit_state": self.circuit_state.value,
            "attempt": self.attempt,
            "consecutive_failures": self.consecutive_failures,
            "failure_category": self.failure_category,
            "reason": self.reason,
        }


class AdaptiveResilienceEngine:
    """
    Combines failure classification, retry policy, circuit state,
    and failure pressure into one resilience decision.

    Decision order:

    1. Open circuit -> STOP.
    2. Non-retryable failure -> STOP.
    3. Maximum attempts reached -> STOP.
    4. High failure pressure -> WAIT with adaptive backoff.
    5. Otherwise -> RETRY using the retry policy.
    """

    def __init__(
        self,
        retry_policy: RetryPolicy | None = None,
        config: AdaptiveResilienceConfig | None = None,
    ) -> None:
        self.retry_policy = retry_policy or RetryPolicy()
        self.config = config or AdaptiveResilienceConfig()

    def decide(
        self,
        classification: FailureClassification,
        circuit: CircuitBreaker,
        *,
        attempt: int,
        consecutive_failures: int,
    ) -> AdaptiveResilienceDecision:
        if attempt < 1:
            raise ValueError(
                "attempt must be at least 1"
            )

        if consecutive_failures < 0:
            raise ValueError(
                "consecutive_failures must be non-negative"
            )

        circuit_state = circuit.state

        if circuit_state == CircuitState.OPEN:
            return AdaptiveResilienceDecision(
                action=ResilienceAction.STOP,
                delay_seconds=0.0,
                retryable=False,
                circuit_state=circuit_state,
                attempt=attempt,
                consecutive_failures=consecutive_failures,
                failure_category=classification.category,
                reason=(
                    "Circuit is open; execution is temporarily "
                    "blocked."
                ),
            )

        if not classification.retryable:
            return AdaptiveResilienceDecision(
                action=ResilienceAction.STOP,
                delay_seconds=0.0,
                retryable=False,
                circuit_state=circuit_state,
                attempt=attempt,
                consecutive_failures=consecutive_failures,
                failure_category=classification.category,
                reason=(
                    "Failure is classified as non-retryable."
                ),
            )

        if attempt >= self.retry_policy.max_attempts:
            return AdaptiveResilienceDecision(
                action=ResilienceAction.STOP,
                delay_seconds=0.0,
                retryable=True,
                circuit_state=circuit_state,
                attempt=attempt,
                consecutive_failures=consecutive_failures,
                failure_category=classification.category,
                reason=(
                    "Maximum retry attempts reached."
                ),
            )

        delay = self.retry_policy.delay_for_attempt(
            attempt + 1
        )

        if (
            consecutive_failures
            >= self.config.failure_pressure_threshold
        ):
            pressure_levels = (
                consecutive_failures
                - self.config.failure_pressure_threshold
                + 1
            )

            adaptive_multiplier = 2 ** pressure_levels

            delay = min(
                delay * adaptive_multiplier,
                self.config.max_adaptive_delay_seconds,
            )

            return AdaptiveResilienceDecision(
                action=ResilienceAction.WAIT,
                delay_seconds=delay,
                retryable=True,
                circuit_state=circuit_state,
                attempt=attempt,
                consecutive_failures=consecutive_failures,
                failure_category=classification.category,
                reason=(
                    "High failure pressure detected; "
                    "adaptive backoff applied."
                ),
            )

        return AdaptiveResilienceDecision(
            action=ResilienceAction.RETRY,
            delay_seconds=delay,
            retryable=True,
            circuit_state=circuit_state,
            attempt=attempt,
            consecutive_failures=consecutive_failures,
            failure_category=classification.category,
            reason=(
                "Failure is retryable; retry policy delay applied."
            ),
        )
