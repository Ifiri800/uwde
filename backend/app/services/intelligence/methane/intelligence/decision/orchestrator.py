from __future__ import annotations

from dataclasses import dataclass

from ..alerts import generate_alert
from ..high_emitters import identify_high_emitter
from ..recommendations import recommend_action
from ..risk import calculate_risk
from .engine import MethaneDecisionEngine
from .models import (
    IntelligenceAlert,
    IntelligenceDecision,
    IntelligenceRecommendation,
    IntelligenceRisk,
)


@dataclass(frozen=True)
class MethaneIntelligenceDecisionResult:
    decision: IntelligenceDecision
    risk: IntelligenceRisk
    alert: IntelligenceAlert | None
    recommendation: IntelligenceRecommendation


class MethaneIntelligenceOrchestrator:
    """Layer 11 integrated methane intelligence engine."""

    def evaluate(
        self,
        entity_id: str,
        *,
        emission_score: float = 0.0,
        emission_rate: float = 0.0,
        leak_probability: float = 0.0,
        equipment_risk: float = 0.0,
        super_emitter: bool = False,
        confidence: float = 0.0,
        evidence_ids: tuple[str, ...] = (),
        signal_ids: tuple[str, ...] = (),
    ) -> MethaneIntelligenceDecisionResult:

        high_emitter = identify_high_emitter(
            entity_id,
            emission_rate,
            confidence=confidence,
        )

        decision = MethaneDecisionEngine().decide(
            entity_id,
            emission_score=max(
                emission_score,
                high_emitter.score if high_emitter.metadata["detected"] else 0.0,
            ),
            leak_probability=leak_probability,
            equipment_risk=equipment_risk,
            super_emitter=super_emitter,
            confidence=confidence,
            evidence_ids=evidence_ids,
            signal_ids=signal_ids,
        )

        risk = calculate_risk(
            entity_id,
            emission_score=decision.score,
            leak_probability=leak_probability,
            equipment_risk=equipment_risk,
            confidence=confidence,
        )

        alert = None

        if decision.priority.value in {"critical", "high"}:
            alert = generate_alert(
                entity_id,
                alert_type="methane_intelligence",
                score=decision.score,
                message=(
                    f"{decision.priority.value.title()} methane intelligence "
                    f"priority detected for {entity_id}."
                ),
                evidence_ids=evidence_ids,
            )

        recommendation = recommend_action(
            entity_id,
            priority=decision.priority,
            rationale=" ".join(decision.rationale),
        )

        return MethaneIntelligenceDecisionResult(
            decision=decision,
            risk=risk,
            alert=alert,
            recommendation=recommendation,
        )


def evaluate_methane_intelligence(
    entity_id: str,
    **kwargs: object,
) -> MethaneIntelligenceDecisionResult:

    return MethaneIntelligenceOrchestrator().evaluate(
        entity_id,
        **kwargs,
    )
