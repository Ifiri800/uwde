from dataclasses import dataclass

from backend.app.services.intelligence.leads.qualification import (
    LeadQualification,
)
from backend.app.services.intelligence.leads.signals import (
    LeadSignal,
    LeadSignalType,
)


@dataclass
class LeadScore:
    company_id: str
    score: float
    priority: str
    signal_score: float
    qualification_score: float
    diversity_score: float

    def __post_init__(self) -> None:
        if not self.company_id:
            raise ValueError("company_id is required")

        for value in (
            self.score,
            self.signal_score,
            self.qualification_score,
            self.diversity_score,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    "score values must be between 0.0 and 1.0"
                )

        if self.priority not in {
            "low",
            "medium",
            "high",
        }:
            raise ValueError(
                "priority must be low, medium, or high"
            )


def score_lead(
    qualification: LeadQualification,
    signals: list[LeadSignal],
) -> LeadScore:
    if not isinstance(
        qualification,
        LeadQualification,
    ):
        raise TypeError(
            "qualification must be a LeadQualification"
        )

    if not signals:
        raise ValueError(
            "At least one lead signal is required"
        )

    if any(
        signal.company_id != qualification.company_id
        for signal in signals
    ):
        raise ValueError(
            "All signals must belong to the qualified company"
        )

    supported_signals = [
        signal
        for signal in signals
        if signal.is_supported
    ]

    if not supported_signals:
        return LeadScore(
            company_id=qualification.company_id,
            score=0.0,
            priority="low",
            signal_score=0.0,
            qualification_score=qualification.score,
            diversity_score=0.0,
        )

    signal_score = sum(
        signal.commercial_strength
        for signal in supported_signals
    ) / len(supported_signals)

    signal_types = {
        signal.signal_type
        for signal in supported_signals
    }

    diversity_score = min(
        1.0,
        len(signal_types) / 3.0,
    )

    score = (
        signal_score * 0.50
        + qualification.score * 0.35
        + diversity_score * 0.15
    )

    score = round(
        min(1.0, max(0.0, score)),
        4,
    )

    if score >= 0.80:
        priority = "high"
    elif score >= 0.60:
        priority = "medium"
    else:
        priority = "low"

    return LeadScore(
        company_id=qualification.company_id,
        score=score,
        priority=priority,
        signal_score=round(signal_score, 4),
        qualification_score=qualification.score,
        diversity_score=round(diversity_score, 4),
    )
