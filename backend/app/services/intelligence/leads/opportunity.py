from dataclasses import dataclass, field
from enum import Enum

from backend.app.services.intelligence.leads.qualification import (
    LeadQualification,
)
from backend.app.services.intelligence.leads.scoring import (
    LeadScore,
)
from backend.app.services.intelligence.leads.signals import (
    LeadSignal,
    LeadSignalType,
)


class LeadOpportunityType(str, Enum):
    PROCUREMENT_OPPORTUNITY = "procurement_opportunity"
    EXPANSION_OPPORTUNITY = "expansion_opportunity"
    SERVICE_DEMAND = "service_demand"
    GROWTH_OPPORTUNITY = "growth_opportunity"
    TECHNOLOGY_OPPORTUNITY = "technology_opportunity"
    PROJECT_OPPORTUNITY = "project_opportunity"
    PARTNERSHIP_OPPORTUNITY = "partnership_opportunity"
    EXECUTIVE_CHANGE = "executive_change"


@dataclass
class LeadOpportunity:
    company_id: str
    opportunity_type: LeadOpportunityType
    score: float
    priority: str
    confidence: float
    recommended_action: str
    signal_types: list[LeadSignalType] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.company_id:
            raise ValueError("company_id is required")

        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                "score must be between 0.0 and 1.0"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        if self.priority not in {
            "low",
            "medium",
            "high",
        }:
            raise ValueError(
                "priority must be low, medium, or high"
            )


def _opportunity_type(
    signal_type: LeadSignalType,
) -> LeadOpportunityType:
    mapping = {
        LeadSignalType.PROCUREMENT:
            LeadOpportunityType.PROCUREMENT_OPPORTUNITY,
        LeadSignalType.EXPANSION:
            LeadOpportunityType.EXPANSION_OPPORTUNITY,
        LeadSignalType.HIRING:
            LeadOpportunityType.SERVICE_DEMAND,
        LeadSignalType.FUNDING:
            LeadOpportunityType.GROWTH_OPPORTUNITY,
        LeadSignalType.TECHNOLOGY_ADOPTION:
            LeadOpportunityType.TECHNOLOGY_OPPORTUNITY,
        LeadSignalType.NEW_PROJECT:
            LeadOpportunityType.PROJECT_OPPORTUNITY,
        LeadSignalType.PARTNERSHIP:
            LeadOpportunityType.PARTNERSHIP_OPPORTUNITY,
        LeadSignalType.EXECUTIVE_CHANGE:
            LeadOpportunityType.EXECUTIVE_CHANGE,
        LeadSignalType.GROWTH:
            LeadOpportunityType.GROWTH_OPPORTUNITY,
    }

    return mapping[signal_type]


def _collect_evidence(
    signals: list[LeadSignal],
) -> list[str]:
    evidence_ids: list[str] = []

    for signal in signals:
        for evidence_id in signal.evidence_ids:
            if evidence_id not in evidence_ids:
                evidence_ids.append(evidence_id)

    return evidence_ids


def create_lead_opportunity(
    *,
    qualification: LeadQualification,
    lead_score: LeadScore,
    signals: list[LeadSignal],
) -> LeadOpportunity:
    if not isinstance(
        qualification,
        LeadQualification,
    ):
        raise TypeError(
            "qualification must be a LeadQualification"
        )

    if not isinstance(
        lead_score,
        LeadScore,
    ):
        raise TypeError(
            "lead_score must be a LeadScore"
        )

    if not signals:
        raise ValueError(
            "At least one lead signal is required"
        )

    if lead_score.company_id != qualification.company_id:
        raise ValueError(
            "Qualification and lead score must belong to the same company"
        )

    company_ids = {
        signal.company_id
        for signal in signals
    }

    if company_ids != {qualification.company_id}:
        raise ValueError(
            "All signals must belong to the qualified company"
        )

    supported_signals = [
        signal
        for signal in signals
        if signal.is_supported
    ]

    if not supported_signals or not qualification.qualified:
        raise ValueError(
            "A qualified lead with supported signals is required"
        )

    strongest_signal = max(
        supported_signals,
        key=lambda signal: (
            signal.commercial_strength,
            signal.confidence,
            signal.strength,
        ),
    )

    opportunity_type = _opportunity_type(
        strongest_signal.signal_type
    )

    evidence_ids = _collect_evidence(
        supported_signals
    )

    confidence = sum(
        signal.confidence
        for signal in supported_signals
    ) / len(supported_signals)

    if lead_score.priority == "high":
        recommended_action = "prioritize_outreach"
    elif lead_score.priority == "medium":
        recommended_action = "review_and_outreach"
    else:
        recommended_action = "monitor"

    reasons = [
        f"{strongest_signal.signal_type.value} is the strongest commercial signal",
        "Opportunity is supported by evidence",
        f"Lead scored {lead_score.score:.4f}",
    ]

    return LeadOpportunity(
        company_id=qualification.company_id,
        opportunity_type=opportunity_type,
        score=lead_score.score,
        priority=lead_score.priority,
        confidence=round(
            min(1.0, max(0.0, confidence)),
            4,
        ),
        recommended_action=recommended_action,
        signal_types=[
            signal.signal_type
            for signal in supported_signals
        ],
        evidence_ids=evidence_ids,
        reasons=reasons,
    )
