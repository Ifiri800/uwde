from backend.app.services.intelligence.methane.intelligence.trends import (
    analyze_trend,
)


def test_increasing_trend():
    result = analyze_trend(
        "facility-001",
        baseline=100.0,
        current=120.0,
    )

    assert result.direction == "increasing"
    assert result.magnitude == 0.2


def test_decreasing_trend():
    result = analyze_trend(
        "facility-001",
        baseline=100.0,
        current=80.0,
    )

    assert result.direction == "decreasing"
