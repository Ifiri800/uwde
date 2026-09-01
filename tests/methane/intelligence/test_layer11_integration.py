from backend.app.services.intelligence.methane.intelligence.decision import (
    MethaneIntelligenceOrchestrator,
)


def test_full_layer_11_orchestration():
    result = MethaneIntelligenceOrchestrator().evaluate(
        "facility-001",
        emission_score=0.95,
        emission_rate=150.0,
        leak_probability=0.90,
        equipment_risk=0.85,
        super_emitter=True,
        confidence=0.92,
    )

    assert result.decision.priority.value == "critical"
    assert result.risk.level.value == "critical"
    assert result.alert is not None
    assert result.recommendation.priority.value == "critical"
