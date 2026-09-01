from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalStatus,
)
from backend.app.services.intelligence.scoring.scorer import (
    SignalScore,
    SignalScorer,
)


@dataclass(frozen=True)
class SignalValidationResult:
    """
    Explainable validation result for an intelligence signal.
    """

    signal_id: str
    is_valid: bool
    reasons: tuple[str, ...]
    score: SignalScore | None = None

    def __post_init__(self) -> None:
        if not self.signal_id.strip():
            raise ValueError("signal_id is required")

        if not self.reasons:
            raise ValueError("at least one validation reason is required")

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "is_valid": self.is_valid,
            "reasons": list(self.reasons),
            "score": (
                {
                    "score": self.score.score,
                    "confidence_component": self.score.confidence_component,
                    "strength_component": self.score.strength_component,
                    "evidence_component": self.score.evidence_component,
                    "corroboration_component": self.score.corroboration_component,
                }
                if self.score
                else None
            ),
        }


class MarketSignalValidator:
    """
    Deterministically validates market intelligence signals.

    Validation checks structural support, signal status, confidence,
    strength, and evidence linkage. Scoring remains delegated to the
    existing SignalScorer.
    """

    MIN_CONFIDENCE = 0.50
    MIN_STRENGTH = 0.30

    def __init__(
        self,
        scorer: SignalScorer | None = None,
    ) -> None:
        self._scorer = scorer or SignalScorer()

    def validate(
        self,
        signal: Signal,
        evidence: list[Evidence] | None = None,
    ) -> SignalValidationResult:
        if not isinstance(signal, Signal):
            raise TypeError("signal must be a Signal")

        if evidence is None:
            evidence_records: list[Evidence] = []
        else:
            if not isinstance(evidence, list):
                raise TypeError("evidence must be a list")

            evidence_records = evidence

        if any(
            not isinstance(item, Evidence)
            for item in evidence_records
        ):
            raise TypeError(
                "evidence must contain only Evidence objects"
            )

        reasons: list[str] = []

        if not signal.entity_id.strip():
            reasons.append("signal entity_id is missing")

        if signal.status in {
            SignalStatus.DISMISSED,
            SignalStatus.EXPIRED,
        }:
            reasons.append(
                f"signal status is {signal.status.value}"
            )

        if signal.confidence < self.MIN_CONFIDENCE:
            reasons.append(
                f"confidence is below {self.MIN_CONFIDENCE:.2f}"
            )

        if signal.strength < self.MIN_STRENGTH:
            reasons.append(
                f"strength is below {self.MIN_STRENGTH:.2f}"
            )

        if not signal.evidence_ids:
            reasons.append("signal has no supporting evidence IDs")
        else:
            evidence_ids = {
                item.evidence_id
                for item in evidence_records
            }

            if not any(
                evidence_id in evidence_ids
                for evidence_id in signal.evidence_ids
            ):
                reasons.append(
                    "signal evidence IDs do not match supplied evidence"
                )

        score = self._scorer.score(
            signal,
            evidence_records,
        )

        if not reasons:
            reasons.append("signal passed all validation checks")

        return SignalValidationResult(
            signal_id=signal.signal_id,
            is_valid=not any(
                reason != "signal passed all validation checks"
                for reason in reasons
            ),
            reasons=tuple(reasons),
            score=score,
        )

    def validate_many(
        self,
        signals: list[Signal],
        evidence: list[Evidence] | None = None,
    ) -> list[SignalValidationResult]:
        if not isinstance(signals, list):
            raise TypeError("signals must be a list")

        return [
            self.validate(signal, evidence)
            for signal in signals
        ]


def validate_market_signal(
    signal: Signal,
    evidence: list[Evidence] | None = None,
) -> SignalValidationResult:
    """
    Convenience function using the default validator.
    """
    return MarketSignalValidator().validate(
        signal,
        evidence,
    )


def validate_market_signals(
    signals: list[Signal],
    evidence: list[Evidence] | None = None,
) -> list[SignalValidationResult]:
    """
    Convenience function for validating multiple signals.
    """
    return MarketSignalValidator().validate_many(
        signals,
        evidence,
    )
