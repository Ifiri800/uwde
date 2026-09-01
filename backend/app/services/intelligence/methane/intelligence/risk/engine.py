from __future__ import annotations

from .models import IntelligenceRisk, RiskLevel


def calculate_risk(
    entity_id: str,
    *,
    emission_score: float = 0.0,
    leak_probability: float = 0.0,
    equipment_risk: float = 0.0,
    confidence: float = 0.0,
) -> IntelligenceRisk:

    components = (
        max(0.0, min(1.0, emission_score)),
        max(0.0, min(1.0, leak_probability)),
        max(0.0, min(1.0, equipment_risk)),
    )

    score = sum(components) / len(components)

    if score >= 0.90:
        level = RiskLevel.CRITICAL
    elif score >= 0.75:
        level = RiskLevel.HIGH
    elif score >= 0.50:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW

    factors = tuple(
        name
        for name, value in (
            ("emission", emission_score),
            ("leak_probability", leak_probability),
            ("equipment", equipment_risk),
        )
        if value >= 0.50
    )

    return IntelligenceRisk(
        entity_id=entity_id,
        score=score,
        level=level,
        factors=factors,
        confidence=max(0.0, min(1.0, confidence)),
    )
