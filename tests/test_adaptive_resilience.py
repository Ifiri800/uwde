from __future__ import annotations

import pytest

from backend.app.services.adaptive_resilience import (
    AdaptiveResilienceConfig,
    AdaptiveResilienceDecision,
    AdaptiveResilienceEngine,
    ResilienceAction,
)

from backend.app.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)

from backend.app.services.pipeline_failure_classifier import (
    FailureClassification,
)

from backend.app.services.pipeline_reliability import (
    RetryPolicy,
)


def make_classification(
    *,
    retryable: bool,
    category: str = "transient",
) -> FailureClassification:
    return FailureClassification(
        category=category,
        retryable=retryable,
        recovery_action="retry" if retryable else "stop",
        recovery_reason="test classification",
        reason="test classification",
        error_type="TestError",
    )


def test_retryable_failure_returns_retry():
    engine = AdaptiveResilienceEngine(
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=1.0,
            max_delay_seconds=10.0,
            backoff_multiplier=2.0,
        )
    )

    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=1,
        consecutive_failures=1,
    )

    assert decision.action == ResilienceAction.RETRY
    assert decision.delay_seconds == 2.0
    assert decision.retryable is True
    assert decision.circuit_state == CircuitState.CLOSED


def test_non_retryable_failure_returns_stop():
    engine = AdaptiveResilienceEngine()
    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(
            retryable=False,
            category="permanent",
        ),
        circuit,
        attempt=1,
        consecutive_failures=1,
    )

    assert decision.action == ResilienceAction.STOP
    assert decision.delay_seconds == 0.0
    assert decision.retryable is False


def test_max_attempts_returns_stop():
    engine = AdaptiveResilienceEngine(
        retry_policy=RetryPolicy(max_attempts=3)
    )

    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=3,
        consecutive_failures=3,
    )

    assert decision.action == ResilienceAction.STOP
    assert "Maximum retry attempts" in decision.reason


def test_open_circuit_returns_stop():
    engine = AdaptiveResilienceEngine()

    circuit = CircuitBreaker(
        "test",
        CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout_seconds=60.0,
        ),
    )

    circuit.record_failure()

    assert circuit.state == CircuitState.OPEN

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=1,
        consecutive_failures=1,
    )

    assert decision.action == ResilienceAction.STOP
    assert decision.circuit_state == CircuitState.OPEN


def test_normal_failure_uses_retry_policy_delay():
    engine = AdaptiveResilienceEngine(
        retry_policy=RetryPolicy(
            max_attempts=5,
            initial_delay_seconds=1.0,
            max_delay_seconds=20.0,
            backoff_multiplier=2.0,
        )
    )

    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=2,
        consecutive_failures=2,
    )

    assert decision.action == ResilienceAction.RETRY
    assert decision.delay_seconds == 4.0


def test_high_failure_pressure_uses_adaptive_backoff():
    engine = AdaptiveResilienceEngine(
        retry_policy=RetryPolicy(
            max_attempts=5,
            initial_delay_seconds=1.0,
            max_delay_seconds=20.0,
            backoff_multiplier=2.0,
        ),
        config=AdaptiveResilienceConfig(
            max_adaptive_delay_seconds=60.0,
            failure_pressure_threshold=3,
        ),
    )

    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=2,
        consecutive_failures=3,
    )

    assert decision.action == ResilienceAction.WAIT
    assert decision.delay_seconds == 8.0
    assert "failure pressure" in decision.reason


def test_adaptive_delay_is_capped():
    engine = AdaptiveResilienceEngine(
        retry_policy=RetryPolicy(
            max_attempts=10,
            initial_delay_seconds=10.0,
            max_delay_seconds=100.0,
            backoff_multiplier=2.0,
        ),
        config=AdaptiveResilienceConfig(
            max_adaptive_delay_seconds=25.0,
            failure_pressure_threshold=2,
        ),
    )

    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=2,
        consecutive_failures=5,
    )

    assert decision.action == ResilienceAction.WAIT
    assert decision.delay_seconds == 25.0


def test_decision_is_serializable():
    engine = AdaptiveResilienceEngine()
    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=1,
        consecutive_failures=1,
    )

    data = decision.to_dict()

    assert data["action"] == "retry"
    assert data["circuit_state"] == "closed"
    assert data["attempt"] == 1
    assert data["consecutive_failures"] == 1


def test_invalid_adaptive_delay_is_rejected():
    with pytest.raises(ValueError):
        AdaptiveResilienceConfig(
            max_adaptive_delay_seconds=-1
        )


def test_invalid_failure_pressure_threshold_is_rejected():
    with pytest.raises(ValueError):
        AdaptiveResilienceConfig(
            failure_pressure_threshold=0
        )


def test_engine_uses_supplied_retry_policy():
    policy = RetryPolicy(
        max_attempts=4,
        initial_delay_seconds=3.0,
        max_delay_seconds=20.0,
        backoff_multiplier=2.0,
    )

    engine = AdaptiveResilienceEngine(
        retry_policy=policy
    )

    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=1,
        consecutive_failures=1,
    )

    assert decision.delay_seconds == 6.0


def test_decision_records_failure_category():
    engine = AdaptiveResilienceEngine()
    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(
            retryable=False,
            category="validation",
        ),
        circuit,
        attempt=1,
        consecutive_failures=1,
    )

    assert decision.failure_category == "validation"


def test_half_open_circuit_can_permit_recovery_probe():
    engine = AdaptiveResilienceEngine()
    circuit = CircuitBreaker(
        "test",
        CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout_seconds=0.0,
        ),
    )

    circuit.record_failure()

    assert circuit.state == CircuitState.HALF_OPEN
    assert circuit.allow_request() is True

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=1,
        consecutive_failures=1,
    )

    assert decision.action == ResilienceAction.RETRY
    assert decision.circuit_state == CircuitState.HALF_OPEN


def test_decision_contains_attempt_information():
    engine = AdaptiveResilienceEngine()
    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=2,
        consecutive_failures=2,
    )

    assert decision.attempt == 2
    assert decision.consecutive_failures == 2


def test_zero_failure_pressure_does_not_trigger_adaptive_wait():
    engine = AdaptiveResilienceEngine(
        config=AdaptiveResilienceConfig(
            failure_pressure_threshold=3
        )
    )

    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=1,
        consecutive_failures=0,
    )

    assert decision.action == ResilienceAction.RETRY


def test_retry_delay_respects_retry_policy_maximum():
    engine = AdaptiveResilienceEngine(
        retry_policy=RetryPolicy(
            max_attempts=5,
            initial_delay_seconds=10.0,
            max_delay_seconds=12.0,
            backoff_multiplier=2.0,
        )
    )

    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(retryable=True),
        circuit,
        attempt=3,
        consecutive_failures=1,
    )

    assert decision.delay_seconds == 12.0


def test_stop_decision_has_zero_delay():
    engine = AdaptiveResilienceEngine()
    circuit = CircuitBreaker("test")

    decision = engine.decide(
        make_classification(retryable=False),
        circuit,
        attempt=1,
        consecutive_failures=1,
    )

    assert decision.action == ResilienceAction.STOP
    assert decision.delay_seconds == 0.0
