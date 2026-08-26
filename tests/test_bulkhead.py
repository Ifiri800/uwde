from __future__ import annotations

import threading
import time

import pytest

from backend.app.services.bulkhead import (
    Bulkhead,
    BulkheadConfig,
    BulkheadRejectedError,
)


def test_bulkhead_starts_empty():
    bulkhead = Bulkhead("test")

    snapshot = bulkhead.snapshot()

    assert snapshot.name == "test"
    assert snapshot.active == 0
    assert snapshot.queued == 0
    assert snapshot.available == 5
    assert snapshot.total_accepted == 0
    assert snapshot.total_rejected == 0
    assert snapshot.total_completed == 0
    assert snapshot.total_failed == 0


def test_bulkhead_allows_capacity():
    bulkhead = Bulkhead(
        "test",
        BulkheadConfig(max_concurrency=2),
    )

    bulkhead.acquire()
    bulkhead.acquire()

    assert bulkhead.active == 2
    assert bulkhead.available == 0

    bulkhead.release()
    bulkhead.release()


def test_bulkhead_rejects_when_capacity_and_queue_are_full():
    bulkhead = Bulkhead(
        "test",
        BulkheadConfig(
            max_concurrency=1,
            max_queue_size=0,
            acquisition_timeout_seconds=0,
        ),
    )

    bulkhead.acquire()

    with pytest.raises(BulkheadRejectedError):
        bulkhead.acquire()

    assert bulkhead.active == 1
    assert bulkhead.snapshot().total_rejected == 1

    bulkhead.release()


def test_bulkhead_release_frees_capacity():
    bulkhead = Bulkhead(
        "test",
        BulkheadConfig(max_concurrency=1),
    )

    bulkhead.acquire()

    assert bulkhead.active == 1

    bulkhead.release()

    assert bulkhead.active == 0
    assert bulkhead.available == 1


def test_execute_runs_operation():
    bulkhead = Bulkhead(
        "test",
        BulkheadConfig(max_concurrency=1),
    )

    result = bulkhead.execute(
        lambda: "success"
    )

    assert result == "success"

    snapshot = bulkhead.snapshot()

    assert snapshot.active == 0
    assert snapshot.total_accepted == 1
    assert snapshot.total_completed == 1
    assert snapshot.total_failed == 0


def test_execute_releases_capacity_after_failure():
    bulkhead = Bulkhead(
        "test",
        BulkheadConfig(max_concurrency=1),
    )

    def failing_operation():
        raise RuntimeError("operation failed")

    with pytest.raises(
        RuntimeError,
        match="operation failed",
    ):
        bulkhead.execute(failing_operation)

    snapshot = bulkhead.snapshot()

    assert snapshot.active == 0
    assert snapshot.available == 1
    assert snapshot.total_accepted == 1
    assert snapshot.total_completed == 1
    assert snapshot.total_failed == 1


def test_rejected_operation_is_not_executed():
    bulkhead = Bulkhead(
        "test",
        BulkheadConfig(
            max_concurrency=1,
            max_queue_size=0,
        ),
    )

    executed = []

    bulkhead.acquire()

    with pytest.raises(BulkheadRejectedError):
        bulkhead.execute(
            lambda: executed.append(True)
        )

    assert executed == []

    bulkhead.release()


def test_release_without_acquire_is_rejected():
    bulkhead = Bulkhead("test")

    with pytest.raises(RuntimeError):
        bulkhead.release()


def test_invalid_concurrency_configuration():
    with pytest.raises(ValueError):
        BulkheadConfig(max_concurrency=0)


def test_invalid_queue_configuration():
    with pytest.raises(ValueError):
        BulkheadConfig(max_queue_size=-1)


def test_invalid_timeout_configuration():
    with pytest.raises(ValueError):
        BulkheadConfig(
            acquisition_timeout_seconds=-1
        )


def test_empty_bulkhead_name_is_rejected():
    with pytest.raises(ValueError):
        Bulkhead("")


def test_whitespace_bulkhead_name_is_rejected():
    with pytest.raises(ValueError):
        Bulkhead("   ")


def test_snapshot_is_serializable():
    bulkhead = Bulkhead("test")

    data = bulkhead.to_dict()

    assert isinstance(data, dict)
    assert data["name"] == "test"
    assert data["active"] == 0
    assert data["queued"] == 0
    assert data["available"] == 5
    assert data["utilization"] == 0.0


def test_utilization_tracks_active_capacity():
    bulkhead = Bulkhead(
        "test",
        BulkheadConfig(max_concurrency=4),
    )

    bulkhead.acquire()
    bulkhead.acquire()

    snapshot = bulkhead.snapshot()

    assert snapshot.utilization == 0.5

    bulkhead.release()
    bulkhead.release()


def test_record_failure_increments_failure_count():
    bulkhead = Bulkhead("test")

    bulkhead.record_failure()

    assert bulkhead.snapshot().total_failed == 1


def test_queue_accepts_waiting_operation():
    bulkhead = Bulkhead(
        "test",
        BulkheadConfig(
            max_concurrency=1,
            max_queue_size=1,
            acquisition_timeout_seconds=2,
        ),
    )

    first_started = threading.Event()
    release_first = threading.Event()
    second_finished = threading.Event()

    def first_operation():
        first_started.set()
        release_first.wait(timeout=2)

    def second_operation():
        second_finished.set()

    first_thread = threading.Thread(
        target=lambda: bulkhead.execute(
            first_operation
        )
    )

    second_thread = threading.Thread(
        target=lambda: bulkhead.execute(
            second_operation
        )
    )

    first_thread.start()

    assert first_started.wait(timeout=2)

    second_thread.start()

    time.sleep(0.1)

    snapshot = bulkhead.snapshot()

    assert snapshot.active == 1
    assert snapshot.queued == 1

    release_first.set()

    first_thread.join(timeout=2)
    second_thread.join(timeout=2)

    assert not first_thread.is_alive()
    assert not second_thread.is_alive()
    assert second_finished.is_set()

    snapshot = bulkhead.snapshot()

    assert snapshot.active == 0
    assert snapshot.queued == 0
    assert snapshot.total_accepted == 2
    assert snapshot.total_completed == 2


def test_queued_operation_times_out():
    bulkhead = Bulkhead(
        "test",
        BulkheadConfig(
            max_concurrency=1,
            max_queue_size=1,
            acquisition_timeout_seconds=0.1,
        ),
    )

    bulkhead.acquire()

    start = time.monotonic()

    with pytest.raises(BulkheadRejectedError):
        bulkhead.acquire()

    elapsed = time.monotonic() - start

    assert elapsed >= 0.08
    assert bulkhead.snapshot().total_rejected == 1

    bulkhead.release()


def test_concurrent_operations_respect_max_concurrency():
    bulkhead = Bulkhead(
        "test",
        BulkheadConfig(
            max_concurrency=2,
            max_queue_size=5,
            acquisition_timeout_seconds=2,
        ),
    )

    active_samples = []
    lock = threading.Lock()
    start_event = threading.Event()
    release_event = threading.Event()

    def operation():
        start_event.wait(timeout=2)

        with lock:
            active_samples.append(
                bulkhead.active
            )

        release_event.wait(timeout=2)

    threads = [
        threading.Thread(
            target=lambda: bulkhead.execute(operation)
        )
        for _ in range(2)
    ]

    for thread in threads:
        thread.start()

    time.sleep(0.1)

    start_event.set()

    time.sleep(0.1)

    assert bulkhead.active == 2
    assert bulkhead.active <= 2

    release_event.set()

    for thread in threads:
        thread.join(timeout=2)

    assert all(
        sample <= 2
        for sample in active_samples
    )
    assert bulkhead.active == 0


def test_configuration_is_immutable():
    config = BulkheadConfig(
        max_concurrency=3,
        max_queue_size=4,
        acquisition_timeout_seconds=1,
    )

    with pytest.raises(Exception):
        config.max_concurrency = 10
