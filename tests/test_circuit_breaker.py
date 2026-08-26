from __future__ import annotations

import time

import pytest

from backend.app.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerRegistry,
    CircuitOpenError,
    CircuitState,
    get_circuit_breaker,
    get_circuit_registry,
)


def test_circuit_starts_closed():
    circuit = CircuitBreaker("test")

    assert circuit.state == CircuitState.CLOSED
    assert circuit.allow_request() is True


def test_circuit_opens_after_failure_threshold():
    circuit = CircuitBreaker(
        "test",
        CircuitBreakerConfig(
            failure_threshold=3,
        ),
    )

    circuit.record_failure()
    circuit.record_failure()

    assert circuit.state == CircuitState.CLOSED

    circuit.record_failure()

    assert circuit.state == CircuitState.OPEN
    assert circuit.allow_request() is False


def test_open_circuit_blocks_call():
    circuit = CircuitBreaker(
        "test",
        CircuitBreakerConfig(
            failure_threshold=1,
        ),
    )

    circuit.record_failure()

    with pytest.raises(CircuitOpenError):
        circuit.call(lambda: "should not execute")


def test_success_resets_consecutive_failures():
    circuit = CircuitBreaker(
        "test",
        CircuitBreakerConfig(
            failure_threshold=3,
        ),
    )

    circuit.record_failure()
    circuit.record_failure()
    circuit.record_success()

    assert circuit.state == CircuitState.CLOSED
    assert circuit.snapshot().consecutive_failures == 0


def test_open_circuit_transitions_to_half_open():
    circuit = CircuitBreaker(
        "test",
        CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout_seconds=0.01,
        ),
    )

    circuit.record_failure()

    assert circuit.state == CircuitState.OPEN

    time.sleep(0.02)

    assert circuit.state == CircuitState.HALF_OPEN


def test_half_open_success_closes_circuit():
    circuit = CircuitBreaker(
        "test",
        CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout_seconds=0.01,
        ),
    )

    circuit.record_failure()

    time.sleep(0.02)

    assert circuit.state == CircuitState.HALF_OPEN
    assert circuit.allow_request() is True

    circuit.record_success()

    assert circuit.state == CircuitState.CLOSED


def test_half_open_failure_reopens_circuit():
    circuit = CircuitBreaker(
        "test",
        CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout_seconds=0.01,
        ),
    )

    circuit.record_failure()

    time.sleep(0.02)

    assert circuit.state == CircuitState.HALF_OPEN
    assert circuit.allow_request() is True

    circuit.record_failure()

    assert circuit.state == CircuitState.OPEN
    assert circuit.allow_request() is False


def test_only_one_half_open_probe_is_allowed():
    circuit = CircuitBreaker(
        "test",
        CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout_seconds=0.01,
        ),
    )

    circuit.record_failure()

    time.sleep(0.02)

    assert circuit.allow_request() is True
    assert circuit.allow_request() is False


def test_call_records_success():
    circuit = CircuitBreaker("test")

    result = circuit.call(
        lambda: "success"
    )

    assert result == "success"

    snapshot = circuit.snapshot()

    assert snapshot.total_successes == 1
    assert snapshot.total_failures == 0


def test_call_records_failure():
    circuit = CircuitBreaker("test")

    with pytest.raises(RuntimeError):
        circuit.call(
            lambda: (_ for _ in ()).throw(
                RuntimeError("failure")
            )
        )

    snapshot = circuit.snapshot()

    assert snapshot.total_successes == 0
    assert snapshot.total_failures == 1


def test_manual_reset_closes_circuit():
    circuit = CircuitBreaker(
        "test",
        CircuitBreakerConfig(
            failure_threshold=1,
        ),
    )

    circuit.record_failure()

    assert circuit.state == CircuitState.OPEN

    circuit.reset()

    assert circuit.state == CircuitState.CLOSED
    assert circuit.allow_request() is True


def test_snapshot_is_serializable():
    import json

    circuit = CircuitBreaker("test")

    circuit.record_success()
    circuit.record_failure()

    data = circuit.to_dict()

    json.dumps(data)

    assert data["name"] == "test"
    assert data["state"] == "closed"
    assert data["total_successes"] == 1
    assert data["total_failures"] == 1


def test_invalid_configuration_is_rejected():
    with pytest.raises(
        ValueError,
        match="failure_threshold must be at least 1",
    ):
        CircuitBreakerConfig(
            failure_threshold=0
        )

    with pytest.raises(
        ValueError,
        match="recovery_timeout_seconds must be non-negative",
    ):
        CircuitBreakerConfig(
            recovery_timeout_seconds=-1
        )

    with pytest.raises(
        ValueError,
        match="success_threshold must be at least 1",
    ):
        CircuitBreakerConfig(
            success_threshold=0
        )


def test_empty_name_is_rejected():
    with pytest.raises(
        ValueError,
        match="name must not be empty",
    ):
        CircuitBreaker("")


def test_registry_returns_same_circuit_for_same_name():
    registry = CircuitBreakerRegistry()

    first = registry.get("example.com")
    second = registry.get("example.com")

    assert first is second


def test_registry_normalizes_circuit_name():
    registry = CircuitBreakerRegistry()

    first = registry.get(" example.com ")
    second = registry.get("example.com")

    assert first is second
    assert first.name == "example.com"


def test_registry_creates_independent_circuits():
    registry = CircuitBreakerRegistry(
        CircuitBreakerConfig(
            failure_threshold=1,
        )
    )

    first = registry.get("example.com")
    second = registry.get("other.example.com")

    first.record_failure()

    assert first.state == CircuitState.OPEN
    assert second.state == CircuitState.CLOSED


def test_registry_snapshot_contains_all_circuits():
    registry = CircuitBreakerRegistry()

    registry.get("example.com")
    registry.get("other.example.com")

    snapshot = registry.snapshot()

    assert set(snapshot) == {
        "example.com",
        "other.example.com",
    }

    assert snapshot["example.com"]["name"] == "example.com"
    assert snapshot["other.example.com"]["name"] == (
        "other.example.com"
    )


def test_registry_reset_resets_named_circuit():
    registry = CircuitBreakerRegistry(
        CircuitBreakerConfig(
            failure_threshold=1,
        )
    )

    circuit = registry.get("example.com")

    circuit.record_failure()

    assert circuit.state == CircuitState.OPEN

    registry.reset("example.com")

    assert circuit.state == CircuitState.CLOSED


def test_registry_clear_removes_all_circuits():
    registry = CircuitBreakerRegistry()

    registry.get("example.com")
    registry.get("other.example.com")

    assert len(registry.snapshot()) == 2

    registry.clear()

    assert registry.snapshot() == {}


def test_registry_rejects_empty_name():
    registry = CircuitBreakerRegistry()

    with pytest.raises(
        ValueError,
        match="circuit name must not be empty",
    ):
        registry.get("   ")


def test_global_registry_returns_persistent_circuit():
    registry = get_circuit_registry()

    registry.clear()

    first = get_circuit_breaker("example.com")
    second = get_circuit_breaker("example.com")

    assert first is second
    assert first.name == "example.com"

    registry.clear()
