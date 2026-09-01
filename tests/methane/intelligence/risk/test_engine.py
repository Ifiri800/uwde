from backend.app.services.intelligence.methane.intelligence.risk import (
    calculate_risk,
)


def test_critical_risk():
    result = calculate_risk(
        "asset-001",
        emission_score=1.0,
        leak_probability=0.95,
        equipment_risk=0.90,
    )

    assert result.level.value == "critical"
    assert result.score >= 0.90
