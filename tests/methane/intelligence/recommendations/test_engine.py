from backend.app.services.intelligence.methane.intelligence.recommendations import (
    recommend_action,
)
from backend.app.services.intelligence.methane.intelligence.decision import (
    DecisionPriority,
)


def test_critical_recommendation():
    result = recommend_action(
        "asset-001",
        priority=DecisionPriority.CRITICAL,
        rationale="High methane risk.",
    )

    assert result.priority == DecisionPriority.CRITICAL
    assert "LDAR" in result.action
