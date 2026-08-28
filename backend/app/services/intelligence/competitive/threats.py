from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from backend.app.services.intelligence.competitive.positioning import (
    CompetitivePositioningResult,
    PositioningDimension,
)
from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import Signal, SignalType


class ThreatLevel(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class ThreatDimension(StrEnum):
    MARKET_ENTRY = "market_entry"
    PRODUCT = "product"
    PRICING = "pricing"
    GEOGRAPHIC_EXPANSION = "geographic_expansion"
    TECHNOLOGY = "technology"
    COMMERCIAL = "commercial"
    PROCUREMENT = "procurement"
    HIRING = "hiring"
    FUNDING = "funding"
    COMPETITIVE_ACTIVITY = "competitive_activity"


SIGNAL_THREAT_MAP: dict[SignalType, ThreatDimension] = {
    SignalType.NEW_PRODUCT: ThreatDimension.PRODUCT,
    SignalType.PRODUCT_LAUNCH: ThreatDimension.PRODUCT,
    SignalType.PRICE_CHANGE: ThreatDimension.PRICING,
    SignalType.COMPANY_EXPANSION: ThreatDimension.GEOGRAPHIC_EXPANSION,
    SignalType.MARKET_GROWTH: ThreatDimension.MARKET_ENTRY,
    SignalType.TECHNOLOGY_ADOPTION: ThreatDimension.TECHNOLOGY,
    SignalType.BUYER_INTENT: ThreatDimension.COMMERCIAL,
    SignalType.PROCUREMENT_SIGNAL: ThreatDimension.PROCUREMENT,
    SignalType.HIRING_SIGNAL: ThreatDimension.HIRING,
    SignalType.FUNDING_SIGNAL: ThreatDimension.FUNDING,
    SignalType.COMPETITOR_CHANGE: ThreatDimension.COMPETITIVE_ACTIVITY,
}


@dataclass(frozen=True)
class CompetitiveThreatAssessment:
    company_id: str
    competitor_id: str
    threat_score: float
    threat_level: ThreatLevel
    confidence: float
    dimensions: tuple[ThreatDimension, ...] = ()
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id is required")

        if not self.competitor_id.strip():
            raise ValueError("competitor_id is required")

        if self.company_id == self.competitor_id:
            raise ValueError(
                "company_id and competitor_id must differ"
            )

        if not 0.0 <= self.threat_score <= 1.0:
            raise ValueError(
                "threat_score must be between 0.0 and 1.0"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "competitor_id": self.competitor_id,
            "threat_score": self.threat_score,
            "threat_level": self.threat_level.value,
            "confidence": self.confidence,
            "dimensions": [
                dimension.value
                for dimension in self.dimensions
            ],
            "signal_ids": list(self.signal_ids),
            "evidence_ids": list(self.evidence_ids),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class CompetitiveThreatResult:
    company_id: str
    threats: tuple[CompetitiveThreatAssessment, ...]
    highest_threat_level: ThreatLevel
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    confidence: float = 0.0
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "threats": [
                threat.to_dict()
                for threat in self.threats
            ],
            "highest_threat_level": self.highest_threat_level.value,
            "signal_ids": list(self.signal_ids),
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
            "reasons": list(self.reasons),
        }


class CompetitiveThreatEngine:
    """
    Deterministically converts competitor positioning and
    intelligence signals into explainable threat assessments.
    """

    LEVEL_THRESHOLDS = (
        (0.85, ThreatLevel.CRITICAL),
        (0.70, ThreatLevel.HIGH),
        (0.50, ThreatLevel.MEDIUM),
        (0.30, ThreatLevel.LOW),
        (0.00, ThreatLevel.MINIMAL),
    )

    DIMENSION_WEIGHTS = {
        ThreatDimension.MARKET_ENTRY: 0.12,
        ThreatDimension.PRODUCT: 0.12,
        ThreatDimension.PRICING: 0.10,
        ThreatDimension.GEOGRAPHIC_EXPANSION: 0.10,
        ThreatDimension.TECHNOLOGY: 0.10,
        ThreatDimension.COMMERCIAL: 0.10,
        ThreatDimension.PROCUREMENT: 0.08,
        ThreatDimension.HIRING: 0.06,
        ThreatDimension.FUNDING: 0.07,
        ThreatDimension.COMPETITIVE_ACTIVITY: 0.15,
    }

    def assess(
        self,
        company_id: str,
        competitor_id: str,
        positioning: CompetitivePositioningResult,
        signals: list[Signal],
        evidence: list[Evidence] | None = None,
    ) -> CompetitiveThreatAssessment:
        if not isinstance(positioning, CompetitivePositioningResult):
            raise TypeError(
                "positioning must be a CompetitivePositioningResult"
            )

        if positioning.company_id != company_id:
            raise ValueError(
                "positioning company_id must match company_id"
            )

        if positioning.competitor_id != competitor_id:
            raise ValueError(
                "positioning competitor_id must match competitor_id"
            )

        if not isinstance(signals, list):
            raise TypeError("signals must be a list")

        if any(
            not isinstance(signal, Signal)
            for signal in signals
        ):
            raise TypeError(
                "signals must contain only Signal objects"
            )

        evidence_records = evidence or []

        if not isinstance(evidence_records, list):
            raise TypeError("evidence must be a list")

        if any(
            not isinstance(item, Evidence)
            for item in evidence_records
        ):
            raise TypeError(
                "evidence must contain only Evidence objects"
            )

        competitor_signals = [
            signal
            for signal in signals
            if signal.entity_id == competitor_id
        ]

        dimensions: list[ThreatDimension] = []
        dimension_scores: dict[ThreatDimension, float] = {}

        for signal in competitor_signals:
            dimension = SIGNAL_THREAT_MAP.get(signal.signal_type)

            if dimension is None:
                continue

            dimensions.append(dimension)

            strength = signal.confidence * max(
                signal.strength,
                0.0,
            )

            dimension_scores[dimension] = max(
                dimension_scores.get(dimension, 0.0),
                strength,
            )

        dimensions = list(dict.fromkeys(dimensions))

        positioning_pressure = max(
            0.0,
            min(
                1.0,
                positioning.overall_score,
            ),
        )

        weighted_activity = sum(
            self.DIMENSION_WEIGHTS[dimension]
            * dimension_scores.get(dimension, 0.0)
            for dimension in ThreatDimension
        )

        activity_coverage = (
            sum(
                self.DIMENSION_WEIGHTS[dimension]
                for dimension in dimensions
            )
            if dimensions
            else 0.0
        )

        threat_score = min(
            1.0,
            round(
                0.60 * positioning_pressure
                + 0.40 * min(
                    1.0,
                    weighted_activity
                    / max(activity_coverage, 0.01),
                ),
                4,
            ),
        )

        signal_ids = tuple(
            signal.signal_id
            for signal in competitor_signals
        )

        evidence_by_id = {
            item.evidence_id: item
            for item in evidence_records
        }

        evidence_ids: list[str] = []

        for signal in competitor_signals:
            for evidence_id in signal.evidence_ids:
                if (
                    evidence_id in evidence_by_id
                    and evidence_id not in evidence_ids
                ):
                    evidence_ids.append(evidence_id)

        confidence = round(
            max(
                (
                    signal.confidence
                    for signal in competitor_signals
                ),
                default=positioning.confidence,
            ),
            4,
        )

        reasons: list[str] = []

        if positioning.overall_score >= 0.70:
            reasons.append(
                "competitor has strong relative positioning"
            )

        for dimension in dimensions:
            reasons.append(
                f"{dimension.value.replace('_', ' ')} activity detected"
            )

        if evidence_ids:
            reasons.append("supporting evidence available")

        if not reasons:
            reasons.append("limited threat indicators detected")

        return CompetitiveThreatAssessment(
            company_id=company_id,
            competitor_id=competitor_id,
            threat_score=threat_score,
            threat_level=self._level(threat_score),
            confidence=confidence,
            dimensions=tuple(dimensions),
            signal_ids=signal_ids,
            evidence_ids=tuple(evidence_ids),
            reasons=tuple(reasons),
        )

    def assess_many(
        self,
        company_id: str,
        positionings: list[CompetitivePositioningResult],
        signals: list[Signal],
        evidence: list[Evidence] | None = None,
    ) -> CompetitiveThreatResult:
        if not isinstance(positionings, list):
            raise TypeError("positionings must be a list")

        threats = tuple(
            self.assess(
                company_id,
                positioning.competitor_id,
                positioning,
                signals,
                evidence,
            )
            for positioning in positionings
        )

        ordered = tuple(
            sorted(
                threats,
                key=lambda threat: (
                    -threat.threat_score,
                    threat.competitor_id,
                ),
            )
        )

        signal_ids = tuple(
            dict.fromkeys(
                signal_id
                for threat in ordered
                for signal_id in threat.signal_ids
            )
        )

        evidence_ids = tuple(
            dict.fromkeys(
                evidence_id
                for threat in ordered
                for evidence_id in threat.evidence_ids
            )
        )

        confidence = round(
            sum(
                threat.confidence
                for threat in ordered
            ) / len(ordered)
            if ordered
            else 0.0,
            4,
        )

        highest = (
            ordered[0].threat_level
            if ordered
            else ThreatLevel.MINIMAL
        )

        reasons = (
            (
                f"{ordered[0].competitor_id} is the highest "
                "competitive threat"
            ,)
            if ordered
            else ("no competitor threats assessed",)
        )

        return CompetitiveThreatResult(
            company_id=company_id,
            threats=ordered,
            highest_threat_level=highest,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            confidence=confidence,
            reasons=reasons,
        )

    @classmethod
    def _level(cls, score: float) -> ThreatLevel:
        for threshold, level in cls.LEVEL_THRESHOLDS:
            if score >= threshold:
                return level

        return ThreatLevel.MINIMAL


def assess_competitive_threat(
    company_id: str,
    competitor_id: str,
    positioning: CompetitivePositioningResult,
    signals: list[Signal],
    evidence: list[Evidence] | None = None,
) -> CompetitiveThreatAssessment:
    return CompetitiveThreatEngine().assess(
        company_id,
        competitor_id,
        positioning,
        signals,
        evidence,
    )


def assess_competitive_threats(
    company_id: str,
    positionings: list[CompetitivePositioningResult],
    signals: list[Signal],
    evidence: list[Evidence] | None = None,
) -> CompetitiveThreatResult:
    return CompetitiveThreatEngine().assess_many(
        company_id,
        positionings,
        signals,
        evidence,
    )
