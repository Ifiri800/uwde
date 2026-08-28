from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)


class OpportunityDetectionType:
    BUYER_INTENT = "buyer_intent"
    PROCUREMENT = "procurement"
    EXPANSION = "expansion"
    SERVICE_DEMAND = "service_demand"
    GROWTH = "growth"
    TECHNOLOGY = "technology"
    PROJECT = "project"
    PARTNERSHIP = "partnership"
    COMPETITIVE = "competitive"


SIGNAL_OPPORTUNITY_MAP: dict[SignalType, str] = {
    SignalType.BUYER_INTENT:
        OpportunityDetectionType.BUYER_INTENT,

    SignalType.PROCUREMENT_SIGNAL:
        OpportunityDetectionType.PROCUREMENT,

    SignalType.COMPANY_EXPANSION:
        OpportunityDetectionType.EXPANSION,

    SignalType.HIRING_SIGNAL:
        OpportunityDetectionType.SERVICE_DEMAND,

    SignalType.FUNDING_SIGNAL:
        OpportunityDetectionType.GROWTH,

    SignalType.TECHNOLOGY_ADOPTION:
        OpportunityDetectionType.TECHNOLOGY,

    SignalType.NEW_PRODUCT:
        OpportunityDetectionType.PROJECT,

    SignalType.PRODUCT_LAUNCH:
        OpportunityDetectionType.PROJECT,

    SignalType.MARKET_GROWTH:
        OpportunityDetectionType.GROWTH,

    SignalType.COMPETITOR_CHANGE:
        OpportunityDetectionType.COMPETITIVE,

    SignalType.TENDER_OPPORTUNITY:
        OpportunityDetectionType.PROCUREMENT,

}


@dataclass(frozen=True)
class OpportunityDetection:
    company_id: str
    opportunity_type: str
    confidence: float
    strength: float
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    detected_at: datetime | None = None
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id is required")

        if not self.opportunity_type.strip():
            raise ValueError(
                "opportunity_type is required"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(
                "strength must be between 0.0 and 1.0"
            )

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "opportunity_type": self.opportunity_type,
            "confidence": self.confidence,
            "strength": self.strength,
            "signal_ids": list(self.signal_ids),
            "evidence_ids": list(self.evidence_ids),
            "detected_at": (
                self.detected_at.isoformat()
                if self.detected_at
                else None
            ),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class OpportunityDetectionResult:
    company_id: str
    opportunities: tuple[OpportunityDetection, ...]
    signals_evaluated: int

    def __post_init__(self) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id is required")

        if self.signals_evaluated < 0:
            raise ValueError(
                "signals_evaluated cannot be negative"
            )

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "opportunities": [
                opportunity.to_dict()
                for opportunity in self.opportunities
            ],
            "signals_evaluated": self.signals_evaluated,
        }


class OpportunityDetectionEngine:
    """
    Converts general intelligence signals into structured
    commercial opportunity detections.

    Signal and evidence records remain the source of truth.
    Detection does not perform qualification, scoring, or
    decision-making.
    """

    def detect(
        self,
        company_id: str,
        signals: list[Signal],
    ) -> OpportunityDetectionResult:
        if not isinstance(company_id, str):
            raise TypeError(
                "company_id must be a string"
            )

        if not company_id.strip():
            raise ValueError(
                "company_id is required"
            )

        if not isinstance(signals, list):
            raise TypeError(
                "signals must be a list"
            )

        if any(
            not isinstance(signal, Signal)
            for signal in signals
        ):
            raise TypeError(
                "signals must contain only Signal objects"
            )

        relevant_signals = [
            signal
            for signal in signals
            if signal.entity_id == company_id
            and signal.signal_type in SIGNAL_OPPORTUNITY_MAP
        ]

        grouped: dict[str, list[Signal]] = {}

        for signal in relevant_signals:
            opportunity_type = SIGNAL_OPPORTUNITY_MAP[
                signal.signal_type
            ]

            grouped.setdefault(
                opportunity_type,
                [],
            ).append(signal)

        opportunities = [
            self._build_opportunity(
                company_id,
                opportunity_type,
                activity_signals,
            )
            for opportunity_type, activity_signals
            in grouped.items()
        ]

        opportunities.sort(
            key=lambda opportunity: (
                -opportunity.strength,
                -opportunity.confidence,
                opportunity.opportunity_type,
            )
        )

        return OpportunityDetectionResult(
            company_id=company_id,
            opportunities=tuple(opportunities),
            signals_evaluated=len(signals),
        )

    @staticmethod
    def _build_opportunity(
        company_id: str,
        opportunity_type: str,
        signals: list[Signal],
    ) -> OpportunityDetection:
        signal_ids = tuple(
            signal.signal_id
            for signal in signals
        )

        evidence_ids: list[str] = []

        for signal in signals:
            for evidence_id in signal.evidence_ids:
                if evidence_id not in evidence_ids:
                    evidence_ids.append(evidence_id)

        confidence = round(
            max(
                signal.confidence
                for signal in signals
            ),
            4,
        )

        strength = round(
            max(
                signal.strength
                for signal in signals
            ),
            4,
        )

        detected_at = max(
            signal.detected_at
            for signal in signals
        )

        reasons = tuple(
            f"{signal.signal_type.value} signal detected"
            for signal in signals
        )

        return OpportunityDetection(
            company_id=company_id,
            opportunity_type=opportunity_type,
            confidence=confidence,
            strength=strength,
            signal_ids=signal_ids,
            evidence_ids=tuple(evidence_ids),
            detected_at=detected_at,
            reasons=reasons,
        )


def detect_opportunities(
    company_id: str,
    signals: list[Signal],
) -> OpportunityDetectionResult:
    """
    Convenience function using the default opportunity
    detection engine."""
    return OpportunityDetectionEngine().detect(
        company_id,
        signals,
    )


