from __future__ import annotations

from collections.abc import Iterable

from .models import (
    DecisionPriority,
    IntelligenceDecision,
)


class MethaneDecisionEngine:
    """Layer 11 decision engine."""

    def decide(
        self,
        entity_id: str,
        *,
        emission_score: float = 0.0,
        leak_probability: float = 0.0,
        equipment_risk: float = 0.0,
        super_emitter: bool = False,
        confidence: float = 0.0,
        evidence_ids: tuple[str, ...] = (),
        signal_ids: tuple[str, ...] = (),
    ) -> IntelligenceDecision:

        if not isinstance(entity_id, str) or not entity_id.strip():
            raise ValueError("entity_id is required")

        values = (
            max(0.0, min(1.0, emission_score)),
            max(0.0, min(1.0, leak_probability)),
            max(0.0, min(1.0, equipment_risk)),
        )

        score = max(values)

        if super_emitter or score >= 0.90:
            priority = DecisionPriority.CRITICAL
        elif score >= 0.75:
            priority = DecisionPriority.HIGH
        elif score >= 0.50:
            priority = DecisionPriority.MEDIUM
        else:
            priority = DecisionPriority.LOW

        rationale = []

        if super_emitter:
            rationale.append("Entity identified as a super-emitter candidate.")

        if leak_probability >= 0.50:
            rationale.append("Leak probability exceeds the decision threshold.")

        if equipment_risk >= 0.50:
            rationale.append("Equipment risk exceeds the decision threshold.")

        if not rationale:
            rationale.append("No elevated methane intelligence signal detected.")

        actions = (
            ("Immediate field confirmation and LDAR prioritization.",)
            if priority == DecisionPriority.CRITICAL
            else ("Continue monitoring and prioritize for review.",)
            if priority == DecisionPriority.HIGH
            else ("Include in routine methane intelligence review.",)
        )

        return IntelligenceDecision(
            entity_id=entity_id,
            decision_type="methane_intelligence",
            priority=priority,
            score=score,
            confidence=max(0.0, min(1.0, confidence)),
            rationale=tuple(rationale),
            recommended_actions=actions,
            evidence_ids=evidence_ids,
            signal_ids=signal_ids,
            metadata={
                "emission_score": emission_score,
                "leak_probability": leak_probability,
                "equipment_risk": equipment_risk,
                "super_emitter": super_emitter,
            },
        )


def make_decision(
    entity_id: str,
    **kwargs: object,
) -> IntelligenceDecision:
    return MethaneDecisionEngine().decide(
        entity_id,
        **kwargs,
    )
