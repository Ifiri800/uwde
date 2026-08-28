from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import Signal


@dataclass(frozen=True)
class SignalScore:
    """
    Explainable intelligence score for a signal.
    """

    score: float
    confidence_component: float
    strength_component: float
    evidence_component: float
    corroboration_component: float

    def __post_init__(self) -> None:
        for value in (
            self.score,
            self.confidence_component,
            self.strength_component,
            self.evidence_component,
            self.corroboration_component,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    "score components must be between 0.0 and 1.0"
                )


class SignalScorer:
    """
    Deterministic and explainable scorer for intelligence signals.

    The initial weighting deliberately favors the signal's own
    confidence and strength while incorporating evidence quality
    and independent corroboration.
    """

    CONFIDENCE_WEIGHT = 0.35
    STRENGTH_WEIGHT = 0.30
    EVIDENCE_WEIGHT = 0.20
    CORROBORATION_WEIGHT = 0.15

    def score(
        self,
        signal: Signal,
        evidence: list[Evidence] | None = None,
    ) -> SignalScore:
        if not isinstance(signal, Signal):
            raise TypeError("signal must be a Signal")

        evidence_records = evidence or []

        confidence_component = signal.confidence
        strength_component = signal.strength

        evidence_component = self._evidence_quality(
            evidence_records
        )

        corroboration_component = self._corroboration(
            signal,
            evidence_records,
        )

        score = (
            confidence_component * self.CONFIDENCE_WEIGHT
            + strength_component * self.STRENGTH_WEIGHT
            + evidence_component * self.EVIDENCE_WEIGHT
            + corroboration_component
            * self.CORROBORATION_WEIGHT
        )

        return SignalScore(
            score=round(score, 6),
            confidence_component=confidence_component,
            strength_component=strength_component,
            evidence_component=evidence_component,
            corroboration_component=corroboration_component,
        )

    @staticmethod
    def _evidence_quality(
        evidence: list[Evidence],
    ) -> float:
        if not evidence:
            return 0.0

        average_confidence = sum(
            item.confidence
            for item in evidence
        ) / len(evidence)

        return min(
            1.0,
            average_confidence,
        )

    @staticmethod
    def _corroboration(
        signal: Signal,
        evidence: list[Evidence],
    ) -> float:
        if not evidence:
            return 0.0

        matching = [
            item
            for item in evidence
            if item.evidence_id in signal.evidence_ids
        ]

        if not matching:
            return 0.0

        # Two or more independent evidence records represent
        # corroboration. The value saturates at 1.0.
        return min(
            1.0,
            len(matching) / 2.0,
        )


def score_signal(
    signal: Signal,
    evidence: list[Evidence] | None = None,
) -> SignalScore:
    """
    Convenience function using the default scorer.
    """

    return SignalScorer().score(
        signal,
        evidence,
    )
