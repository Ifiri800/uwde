from __future__ import annotations

from .models import (
    DecisionPriority,
    IntelligenceRecommendation,
)


def recommend_action(
    entity_id: str,
    *,
    priority: DecisionPriority,
    rationale: str,
) -> IntelligenceRecommendation:

    if priority == DecisionPriority.CRITICAL:
        action = "Immediate LDAR confirmation, quantification and repair."
        outcome = "Rapid confirmation and reduction of methane emissions."
    elif priority == DecisionPriority.HIGH:
        action = "Prioritize field investigation and LDAR inspection."
        outcome = "Early detection and mitigation of elevated emissions."
    elif priority == DecisionPriority.MEDIUM:
        action = "Schedule targeted monitoring."
        outcome = "Improved evidence and risk characterization."
    else:
        action = "Continue routine monitoring."
        outcome = "Maintain surveillance and data continuity."

    return IntelligenceRecommendation(
        recommendation_id=f"recommendation-{entity_id}",
        entity_id=entity_id,
        action=action,
        priority=priority,
        rationale=rationale,
        expected_outcome=outcome,
    )
