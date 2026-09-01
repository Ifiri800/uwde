from __future__ import annotations

from .models import DecisionPriority, IntelligenceDecision


def identify_high_emitter(
    entity_id: str,
    emission_rate: float,
    *,
    threshold: float = 100.0,
    confidence: float = 1.0,
) -> IntelligenceDecision:

    if emission_rate < 0:
        raise ValueError("emission_rate cannot be negative")

    detected = emission_rate >= threshold

    return IntelligenceDecision(
        entity_id=entity_id,
        decision_type="high_emitter",
        priority=(
            DecisionPriority.CRITICAL
            if detected
            else DecisionPriority.LOW
        ),
        score=min(emission_rate / threshold, 1.0)
        if threshold > 0
        else 1.0,
        confidence=confidence,
        rationale=(
            (
                f"Emission rate {emission_rate} meets or exceeds "
                f"the threshold of {threshold}.",
            )
            if detected
            else (
                f"Emission rate {emission_rate} is below "
                f"the threshold of {threshold}.",
            )
        ),
        recommended_actions=(
            ("Prioritize LDAR confirmation and quantification.",)
            if detected
            else ()
        ),
        metadata={
            "emission_rate": emission_rate,
            "threshold": threshold,
            "detected": detected,
        },
    )
