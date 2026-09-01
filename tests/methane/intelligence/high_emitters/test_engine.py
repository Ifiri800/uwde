from backend.app.services.intelligence.methane.intelligence.high_emitters import (
    identify_high_emitter,
)


def test_high_emitter_detected():
    result = identify_high_emitter(
        "facility-001",
        150.0,
        threshold=100.0,
    )

    assert result.metadata["detected"] is True
    assert result.priority.value == "critical"


def test_high_emitter_not_detected():
    result = identify_high_emitter(
        "facility-001",
        50.0,
        threshold=100.0,
    )

    assert result.metadata["detected"] is False
