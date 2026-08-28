from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)


class RiskDetectionType:
    COMPETITIVE = "competitive"
    PRICING = "pricing"
    PRODUCT = "product"
    MARKET = "market"
    TECHNOLOGY = "technology"
    GROWTH = "growth"


SIGNAL_RISK_MAP: dict[SignalType, str] = {
    SignalType.COMPETITOR_CHANGE:
        RiskDetectionType.COMPETITIVE,

    SignalType.PRICE_CHANGE:
        RiskDetectionType.PRICING,

    SignalType.NEW_PRODUCT:
        RiskDetectionType.PRODUCT,

    SignalType.PRODUCT_LAUNCH:
        RiskDetectionType.PRODUCT,

    SignalType.MARKET_GROWTH:
        RiskDetectionType.MARKET,

    SignalType.TECHNOLOGY_ADOPTION:
        RiskDetectionType.TECHNOLOGY,

    SignalType.COMPANY_EXPANSION:
        RiskDetectionType.GROWTH,

    SignalType.NEW_COMPANY:
        RiskDetectionType.COMPETITIVE,
}


@dataclass(frozen=True)
class RiskDetection:
    company_id: str
    risk_type: str
    confidence: float
    strength: float
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    detected_at: datetime | None = None
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.company_id, str):
            raise TypeError("company_id must be a string")

        if not self.company_id.strip():
            raise ValueError("company_id is required")

        if not isinstance(self.risk_type, str):
            raise TypeError("risk_type must be a string")

        if not self.risk_type.strip():
            raise ValueError("risk_type is required")

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
            "risk_type": self.risk_type,
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
class RiskDetectionResult:
    company_id: str
    risks: tuple[RiskDetection, ...]
    signals_evaluated: int

    def __post_init__(self) -> None:
        if not isinstance(self.company_id, str):
            raise TypeError("company_id must be a string")

        if not self.company_id.strip():
            raise ValueError("company_id is required")

        if self.signals_evaluated < 0:
            raise ValueError(
                "signals_evaluated cannot be negative"
            )

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "risks": [
                risk.to_dict()
                for risk in self.risks
            ],
            "signals_evaluated": self.signals_evaluated,
        }


class RiskDetectionEngine:
    """
    Converts intelligence signals into structured risk detections.

    Detection identifies potential risk dimensions only.
    Risk scoring, prioritization, mitigation, and decision-making
    belong to later intelligence layers.
    """

    def detect(
        self,
        company_id: str,
        signals: list[Signal],
    ) -> RiskDetectionResult:
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
            if (
                signal.entity_id == company_id
                and signal.signal_type in SIGNAL_RISK_MAP
            )
        ]

        grouped: dict[str, list[Signal]] = {}

        for signal in relevant_signals:
            risk_type = SIGNAL_RISK_MAP[
                signal.signal_type
            ]

            grouped.setdefault(
                risk_type,
                [],
            ).append(signal)

        risks = [
            self._build_risk(
                company_id,
                risk_type,
                risk_signals,
            )
            for risk_type, risk_signals
            in grouped.items()
        ]

        risks.sort(
            key=lambda risk: (
                -risk.strength,
                -risk.confidence,
                risk.risk_type,
            )
        )

        return RiskDetectionResult(
            company_id=company_id,
            risks=tuple(risks),
            signals_evaluated=len(signals),
        )

    @staticmethod
    def _build_risk(
        company_id: str,
        risk_type: str,
        signals: list[Signal],
    ) -> RiskDetection:
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
            f"{signal.signal_type.value} signal indicates potential "
            f"{risk_type} risk"
            for signal in signals
        )

        return RiskDetection(
            company_id=company_id,
            risk_type=risk_type,
            confidence=confidence,
            strength=strength,
            signal_ids=signal_ids,
            evidence_ids=tuple(evidence_ids),
            detected_at=detected_at,
            reasons=reasons,
        )


def detect_risks(
    company_id: str,
    signals: list[Signal],
) -> RiskDetectionResult:
    """
    Convenience function using the default risk detection engine.
    """
    return RiskDetectionEngine().detect(
        company_id,
        signals,
    )
