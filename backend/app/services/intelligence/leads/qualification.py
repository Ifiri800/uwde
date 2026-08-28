from dataclasses import dataclass

from backend.app.services.intelligence.leads.signals import LeadSignal


@dataclass
class LeadQualification:
    company_id: str
    qualified: bool
    score: float
    reasons: list[str]

    def __post_init__(self) -> None:
        if not self.company_id:
            raise ValueError("company_id is required")

        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                "score must be between 0.0 and 1.0"
            )


def qualify_lead(
    signals: list[LeadSignal],
    *,
    minimum_score: float = 0.60,
) -> LeadQualification:
    if not signals:
        raise ValueError(
            "At least one lead signal is required"
        )

    company_ids = {
        signal.company_id
        for signal in signals
    }

    if len(company_ids) != 1:
        raise ValueError(
            "All signals must belong to the same company"
        )

    company_id = signals[0].company_id

    supported_signals = [
        signal
        for signal in signals
        if signal.is_supported
    ]

    if not supported_signals:
        return LeadQualification(
            company_id=company_id,
            qualified=False,
            score=0.0,
            reasons=[
                "No supported lead signals"
            ],
        )

    signal_scores = [
        signal.commercial_strength
        for signal in supported_signals
    ]

    average_score = sum(signal_scores) / len(signal_scores)

    corroboration_bonus = min(
        0.15,
        max(0, len(supported_signals) - 1) * 0.05,
    )

    score = min(
        1.0,
        average_score + corroboration_bonus,
    )

    reasons = [
        f"{signal.signal_type.value} signal detected"
        for signal in supported_signals
    ]

    if len(supported_signals) > 1:
        reasons.append(
            "Multiple supported signals corroborate commercial activity"
        )

    qualified = score >= minimum_score

    if qualified:
        reasons.append(
            "Lead meets the commercial qualification threshold"
        )
    else:
        reasons.append(
            "Lead does not meet the commercial qualification threshold"
        )

    return LeadQualification(
        company_id=company_id,
        qualified=qualified,
        score=round(score, 4),
        reasons=reasons,
    )
