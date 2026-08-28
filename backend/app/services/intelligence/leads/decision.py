from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.services.intelligence.leads.signals import (
    LeadSignal,
)


@dataclass(frozen=True)
class LeadDecision:
    company_id: str
    qualified: bool
    priority: str
    confidence: float
    recommended_action: str
    evidence_ids: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def _validate_signals(
    company_id: str,
    signals: list[LeadSignal],
) -> None:
    if not signals:
        raise ValueError(
            "At least one lead signal is required."
        )

    companies = {
        signal.company_id
        for signal in signals
    }

    if companies != {company_id}:
        raise ValueError(
            "All lead signals must belong to the specified company."
        )


def _collect_evidence(
    signals: list[LeadSignal],
) -> list[str]:
    evidence_ids: list[str] = []

    for signal in signals:
        for evidence_id in signal.evidence_ids:
            if evidence_id not in evidence_ids:
                evidence_ids.append(evidence_id)

    return evidence_ids


def _calculate_confidence(
    signals: list[LeadSignal],
) -> float:
    if not signals:
        return 0.0

    supported = [
        signal
        for signal in signals
        if signal.evidence_ids
    ]

    if not supported:
        return 0.0

    confidence = sum(
        signal.confidence
        for signal in supported
    ) / len(supported)

    return min(
        max(confidence, 0.0),
        1.0,
    )


def _priority_from_score(
    score: float,
) -> str:
    if score >= 0.80:
        return "high"

    if score >= 0.60:
        return "medium"

    return "low"


def decide_lead(
    *,
    company_id: str,
    signals: list[LeadSignal],
    qualification_score: float,
) -> LeadDecision:
    _validate_signals(
        company_id,
        signals,
    )

    if not 0.0 <= qualification_score <= 1.0:
        raise ValueError(
            "qualification_score must be between 0 and 1."
        )

    evidence_ids = _collect_evidence(
        signals
    )

    confidence = _calculate_confidence(
        signals
    )

    supported_signals = [
        signal
        for signal in signals
        if signal.evidence_ids
    ]

    qualified = (
        qualification_score >= 0.60
        and bool(supported_signals)
    )

    if not qualified:
        return LeadDecision(
            company_id=company_id,
            qualified=False,
            priority="low",
            confidence=confidence,
            recommended_action="monitor",
            evidence_ids=evidence_ids,
            reasons=[
                "Lead does not currently meet the qualification threshold."
            ],
        )

    priority = _priority_from_score(
        qualification_score
    )

    reasons = [
        f"{len(supported_signals)} supported commercial signal(s) detected",
        "Lead meets the commercial qualification threshold",
    ]

    if priority == "high":
        recommended_action = "prioritize_outreach"
    elif priority == "medium":
        recommended_action = "review_and_outreach"
    else:
        recommended_action = "monitor"

    return LeadDecision(
        company_id=company_id,
        qualified=True,
        priority=priority,
        confidence=confidence,
        recommended_action=recommended_action,
        evidence_ids=evidence_ids,
        reasons=reasons,
    )
