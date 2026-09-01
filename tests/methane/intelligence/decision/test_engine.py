from backend.app.services.intelligence.methane.intelligence.decision import (
    DecisionPriority,
    MethaneDecisionEngine,
)


def test_decision_engine_identifies_critical_entity():
    result = MethaneDecisionEngine().decide(
        "asset-001",
        emission_score=0.95,
        leak_probability=0.80,
        confidence=0.90,
    )

    assert result.priority == DecisionPriority.CRITICAL
    assert result.score == 0.95
    assert result.confidence == 0.90
