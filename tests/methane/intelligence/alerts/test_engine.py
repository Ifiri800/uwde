from backend.app.services.intelligence.methane.intelligence.alerts import (
    generate_alert,
)


def test_critical_alert():
    result = generate_alert(
        "asset-001",
        alert_type="super_emitter",
        score=0.95,
        message="Super-emitter candidate detected.",
    )

    assert result.priority.value == "critical"
    assert result.entity_id == "asset-001"
