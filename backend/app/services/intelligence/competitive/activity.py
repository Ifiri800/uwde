from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.app.services.intelligence.domain.entities import Company
from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import Signal, SignalType


class CompetitorActivityType:
    PRODUCT_ACTIVITY = "product_activity"
    PRICING_ACTIVITY = "pricing_activity"
    HIRING_ACTIVITY = "hiring_activity"
    FUNDING_ACTIVITY = "funding_activity"
    EXPANSION_ACTIVITY = "expansion_activity"
    TECHNOLOGY_ACTIVITY = "technology_activity"
    COMPETITIVE_ACTIVITY = "competitive_activity"
    COMMERCIAL_ACTIVITY = "commercial_activity"
    PARTNERSHIP_ACTIVITY = "partnership_activity"
    PROCUREMENT_ACTIVITY = "procurement_activity"


SIGNAL_ACTIVITY_MAP: dict[SignalType, str] = {
    SignalType.NEW_PRODUCT: CompetitorActivityType.PRODUCT_ACTIVITY,
    SignalType.PRODUCT_LAUNCH: CompetitorActivityType.PRODUCT_ACTIVITY,
    SignalType.PRICE_CHANGE: CompetitorActivityType.PRICING_ACTIVITY,
    SignalType.HIRING_SIGNAL: CompetitorActivityType.HIRING_ACTIVITY,
    SignalType.FUNDING_SIGNAL: CompetitorActivityType.FUNDING_ACTIVITY,
    SignalType.COMPANY_EXPANSION: CompetitorActivityType.EXPANSION_ACTIVITY,
    SignalType.MARKET_GROWTH: CompetitorActivityType.EXPANSION_ACTIVITY,
    SignalType.TECHNOLOGY_ADOPTION: CompetitorActivityType.TECHNOLOGY_ACTIVITY,
    SignalType.COMPETITOR_CHANGE: CompetitorActivityType.COMPETITIVE_ACTIVITY,
    SignalType.BUYER_INTENT: CompetitorActivityType.COMMERCIAL_ACTIVITY,
    SignalType.PROCUREMENT_SIGNAL: CompetitorActivityType.PROCUREMENT_ACTIVITY,
}


@dataclass(frozen=True)
class CompetitorActivity:
    company_id: str
    activity_type: str
    confidence: float
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    detected_at: datetime | None = None
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id is required")

        if not self.activity_type.strip():
            raise ValueError("activity_type is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "activity_type": self.activity_type,
            "confidence": self.confidence,
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
class CompetitorActivityResult:
    activities: tuple[CompetitorActivity, ...]
    signals_evaluated: int

    def __post_init__(self) -> None:
        if self.signals_evaluated < 0:
            raise ValueError(
                "signals_evaluated cannot be negative"
            )

    def to_dict(self) -> dict:
        return {
            "activities": [
                activity.to_dict()
                for activity in self.activities
            ],
            "signals_evaluated": self.signals_evaluated,
        }


class CompetitorActivityAnalyzer:
    """
    Deterministically converts intelligence signals into
    competitor activity records.

    Existing Signal and Evidence records remain the source of truth.
    This layer only interprets and organizes them for competitive
    intelligence.
    """

    def analyze(
        self,
        company: Company,
        signals: list[Signal],
        evidence: list[Evidence] | None = None,
    ) -> CompetitorActivityResult:
        if not isinstance(company, Company):
            raise TypeError("company must be a Company")

        if not isinstance(signals, list):
            raise TypeError("signals must be a list")

        if any(
            not isinstance(signal, Signal)
            for signal in signals
        ):
            raise TypeError(
                "signals must contain only Signal objects"
            )

        if evidence is not None:
            if not isinstance(evidence, list):
                raise TypeError("evidence must be a list")

            if any(
                not isinstance(item, Evidence)
                for item in evidence
            ):
                raise TypeError(
                    "evidence must contain only Evidence objects"
                )

        evidence_records = evidence or []

        relevant_signals = [
            signal
            for signal in signals
            if signal.entity_id == company.entity_id
            and signal.signal_type in SIGNAL_ACTIVITY_MAP
        ]

        grouped: dict[str, list[Signal]] = {}

        for signal in relevant_signals:
            activity_type = SIGNAL_ACTIVITY_MAP[
                signal.signal_type
            ]
            grouped.setdefault(activity_type, []).append(signal)

        activities: list[CompetitorActivity] = []

        evidence_by_id = {
            item.evidence_id: item
            for item in evidence_records
        }

        for activity_type, activity_signals in grouped.items():
            activities.append(
                self._build_activity(
                    company.entity_id,
                    activity_type,
                    activity_signals,
                    evidence_by_id,
                )
            )

        return CompetitorActivityResult(
            activities=tuple(activities),
            signals_evaluated=len(signals),
        )

    def _build_activity(
        self,
        company_id: str,
        activity_type: str,
        signals: list[Signal],
        evidence_by_id: dict[str, Evidence],
    ) -> CompetitorActivity:
        signal_ids = tuple(
            signal.signal_id
            for signal in signals
        )

        evidence_ids: list[str] = []

        for signal in signals:
            for evidence_id in signal.evidence_ids:
                if (
                    evidence_id in evidence_by_id
                    and evidence_id not in evidence_ids
                ):
                    evidence_ids.append(evidence_id)

        confidence = round(
            max(signal.confidence for signal in signals),
            4,
        )

        detected_at = max(
            signal.detected_at
            for signal in signals
        )

        reasons = tuple(
            f"{signal.signal_type.value} detected"
            for signal in signals
        )

        return CompetitorActivity(
            company_id=company_id,
            activity_type=activity_type,
            confidence=confidence,
            signal_ids=signal_ids,
            evidence_ids=tuple(evidence_ids),
            detected_at=detected_at,
            reasons=reasons,
        )


def analyze_competitor_activity(
    company: Company,
    signals: list[Signal],
    evidence: list[Evidence] | None = None,
) -> CompetitorActivityResult:
    """
    Convenience function using the default activity analyzer.
    """
    return CompetitorActivityAnalyzer().analyze(
        company,
        signals,
        evidence,
    )
